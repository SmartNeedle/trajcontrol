import numpy as np
import rclpy

from cv_bridge import CvBridge
from cv_bridge.core import CvBridge
from geometry_msgs.msg import PoseArray, PoseStamped, Quaternion
from rclpy.node import Node
from sensor_msgs.msg import Image
from transforms3d.euler import euler2quat

class EstimatorNode(Node):

    def __init__(self):
        super().__init__('estimator_node')

        #Topics from Stage node
        self.subscription_stage2 = self.create_subscription(PoseStamped, '/stage/state/needle_pose', self.needle_pose_callback, 10)
        self.subscription_stage2  # prevent unused variable warning

        #Topics from UI node
        self.subscription_UI = self.create_subscription(PoseStamped, '/subject/state/skin_entry', self.entry_point_callback, 10)
        self.subscription_UI  # prevent unused variable warning

        #Topics from Sensor node
        self.subscription_sensor = self.create_subscription(PoseArray, '/needle/state/shape', self.needle_shape_callback, 10)
        self.subscription_sensor  # prevent unused variable warning

        #Published topics
        self.publisher_jacobian = self.create_publisher(Image, '/needle/state/jacobian', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_jacobian_callback)
        
        self.X = np.zeros((7,1))
        self.deltaX = np.zeros((7,1))

        self.Z_hat = np.zeros((7,1))
        self.deltaZ = np.zeros((7,1))

        # Initialize Jacobian with estimated values from previous experiments
        # (Alternative: initialize with values from first two sets of sensor and stage data)
        self.J = np.array([(-0.3482, 0.1089, 0.0893,-0.1670, 0.1967, 0.0913, 0.1103),
                  ( 0.3594, 0.1332,-0.2593, 0.1975, 0.7322, 0.7989, 0.0794),
                  (-0.1714, 0.0723, 0.1597, 0.8766, 0.0610,-0.4968, 0.2415),
                  ( 0.0003, 0.0000,-0.0005, 0.0079, 0.0007,-0.0025, 0.0021),
                  (-0.0004,-0.0001, 0.0006,-0.0077,-0.0006, 0.0025,-0.0020),
                  (-0.0017,-0.0006, 0.0009, 0.0040, 0.0083, 0.0053,-0.0007),
                  (0, 0, 0, 0, 0, 0, 0)])

        self.i = 0

    # Get current entry point from UI node
    def entry_point_callback(self, msg):
        ##########################################
        # TODO: Define transform from stage to needle frame
        ##########################################
        entry_point = msg.pose.position

        self.get_logger().info('Listening UI - Skin entry point: x=%f, y=%f, z=%f in %s frame'  % (entry_point.x, entry_point.y, \
            entry_point.z, msg.header.frame_id))


    # Get current needle_pose from Stage node
    # Perform estimator input X ("Prediction")
    # X = [x_stage, y_needle_depth, z_stage, q_needle_roll]
    def needle_pose_callback(self, msg):
        ##########################################
        # TODO: Verify timestamp to match Z
        ##########################################
        needle = msg.pose
        
        X = np.array([[needle.position.x, needle.position.y, needle.position.z, needle.orientation.x, \
            needle.orientation.y, needle.orientation.z, needle.orientation.w]]).T

        self.deltaX = X - self.X
        self.X = X

        deltaZ_hat = np.matmul(self.J, self.deltaX)
        self.Z_hat = deltaZ_hat + self.Z_hat

        # Normalize unit quaternion
        self.Z_hat[3:7] = self.Z_hat[3:7]/np.linalg.norm(self.Z_hat[3:7])

        self.get_logger().info('Z_hat pred: %s in %s frame' % (self.Z_hat.T, msg.header.frame_id))

    # Get current needle shape from FBG sensor measurements
    # Perform estimator "correction"
    # Z = [x_tip, y_tip, z_tip, q_tip] (Obs: for q, roll=pitch)
    def needle_shape_callback(self, msg):
        ##########################################
        # TODO: Verify timestamp to match X
        ##########################################
        shape = msg.poses
        
        # From shape, get measured Z
        N = len(shape)
        if (N==1):
            q = [1, 0, 0, 0]
        else:
            tip = np.array([shape[N-1].position.x, shape[N-1].position.y, shape[N-1].position.z])
            ptip = np.array([shape[N-2].position.x, shape[N-2].position.y, shape[N-2].position.z])
            dir = tip - ptip
            yaw = np.arctan2(dir[1], dir[0])
            pitch = np.arcsin(dir[2])
            roll = pitch
            q = euler2quat(yaw, roll, pitch, 'rzyx')

        Z = np.array([[shape[N-1].position.x, shape[N-1].position.y, shape[N-1].position.z, \
            q[0], q[1], q[2], q[3]]]).T

        self.Z_hat = Z

        self.get_logger().info('Z_hat corr: %s in %s frame' % (self.Z_hat.T, msg.header.frame_id))

    # Publish current Jacobian matrix
    # Update estimate Z_hat
    # Calculate Jacobian from current estimate Z_hat
    def timer_jacobian_callback(self):

        ##########################################
        # TODO: Update Jacobian
        ##########################################

        msg = CvBridge().cv2_to_imgmsg(self.J)
        self.publisher_jacobian.publish(msg)
        self.get_logger().info('Publish - Jacobian: %s' %  self.J)
        self.i += 1


    def normalize_unit_quaternion(q):
        return q/np.norm(q); 

def main(args=None):
    rclpy.init(args=args)

    estimator_node = EstimatorNode()

    rclpy.spin(estimator_node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    estimator_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
