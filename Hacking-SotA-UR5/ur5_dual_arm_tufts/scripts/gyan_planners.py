#!/usr/bin/env python
import rospy
import moveit_commander
import tf
import rospkg
import os
import numpy
import time

from gazebo_msgs.srv import (
    SpawnModel,
    DeleteModel,
)

from geometry_msgs.msg import (
    PoseStamped,
    Pose,
    Point,
    Quaternion,
)

rospy.init_node('planners', anonymous=True)

robot = moveit_commander.RobotCommander()
arm_group = moveit_commander.MoveGroupCommander("manipulator")
grp_group = moveit_commander.MoveGroupCommander("gripper")
scene = moveit_commander.PlanningSceneInterface()


planner = "BKPIECE"

arm_group.set_planner_id(planner)
print("Current Planner: ", planner)

# You can get the reference frame for a certain group by executing this line:
print "Arm Reference frame: %s" % arm_group.get_planning_frame()
print "Gripper Reference frame: %s" % grp_group.get_planning_frame()

# You can get the end-effector link for a certaing group executing this line:
print "Arm End effector: %s" % arm_group.get_end_effector_link()
print "Gripper End effector: %s" % grp_group.get_end_effector_link()

# You can get a list with all the groups of the robot like this:
print "Robot Groups:"
print robot.get_group_names()

# You can get the current values of the joints like this:
print "Arm Current Joint Values:"
print arm_group.get_current_joint_values()
print "Gripper Current Joint Values:"
print grp_group.get_current_joint_values()

# You can also get the current Pose of the end-effector of the robot like this:
print "Arm Current Pose:"
print arm_group.get_current_pose()

# Finally, you can check the general status of the robot like this:
print "Robot State:"
print robot.get_current_state()


def spawn_gazebo_model(model_path, model_name, model_pose, reference_frame="world"):
  """
  Spawn model in gazebo
  """
  model_xml = ''
  with open(model_path, "r") as model_file:
    model_xml = model_file.read().replace('\n', '')
  rospy.wait_for_service('/gazebo/spawn_urdf_model')
  try:
    spawn_urdf = rospy.ServiceProxy('/gazebo/spawn_urdf_model', SpawnModel)
    resp_urdf = spawn_urdf(model_name, model_xml, "/", model_pose, reference_frame)
  except rospy.ServiceException, e:
    rospy.logerr("Spawn URDF service call failed: {0}".format(e))

def delete_gazebo_model(models):
  """
  Delete model in gazebo
  """
  try:
    delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)
    for a_model in models:
      resp_delete = delete_model(a_model)
  except rospy.ServiceException, e:
    rospy.loginfo("Delete Model service call failed: {0}".format(e))

rospack = rospkg.RosPack()
pack_path = rospack.get_path('ur5_single_arm_tufts')


table_path = pack_path+os.sep+'urdf'+os.sep+'objects'+os.sep+'table.urdf'
table_name = 'table'
table_pose = Pose(position=Point(x=0.85, y=0.0, z=0.70))

block_path = pack_path+os.sep+'urdf'+os.sep+'objects'+os.sep+'block.urdf'
block_name = 'block'
block_pose = Pose(position=Point(x=0.4, y=0.0, z=0.75))

#delete_gazebo_model([table_name, block_name])
#spawn_gazebo_model(table_path, table_name, table_pose)
#spawn_gazebo_model(block_path, block_name, block_pose)



"""
The Lenght of gripper is ~0.15
Min. reachable z value on the table is 0.9 from downOrientation
Min. reachable x on table: 0.37

Max. reachable y on table: 0.46

Right front corner of table
  x: 1.3552107811
  y: 0.493778288364
  z: 0.719269096851

Right back corner of table
  x: 0.352727115154
  y: 0.504722833633
  z: 0.714043438435

Left front corner of table
  x: 1.35521054268
  y: -0.491892397404
  z: 0.717385590076

Left back corner of table
  x: 0.363544255495
  y: -0.502857685089
  z: 0.721333742142
"""


arm_group.set_named_target('pickup')
arm_group.go(wait=True)
print("Pickup Point")

pose = arm_group.get_current_pose().pose
# Max x points
# pose.position.x = 0.9 #0.9
# pose.position.y = -0.2 # -0.1 to 0.1
# pose.position.z = 0.89

# Min x points
# pose.position.x = 0.37 #0.37
# pose.position.y = -0.46 # -0.46 to 0.46
# pose.position.z = 0.89

scene.remove_world_object("obstacle")

# Start point
pose.position.x = 0.4
pose.position.y = -0.2
pose.position.z = 1

downOrientation = tf.transformations.quaternion_from_euler(0, 3.1415/2, 0)
print("downOrientation: ", downOrientation)
pose.orientation.x = downOrientation[0]
pose.orientation.y = downOrientation[1]
pose.orientation.z = downOrientation[2]
pose.orientation.w = downOrientation[3]

pose_A = pose

arm_group.set_pose_target(pose_A)
arm_group.go(wait=True)
print("Start point")

# End point
pose.position.x = 0.4
pose.position.y = 0.2
pose.position.z = 1

downOrientation = tf.transformations.quaternion_from_euler(0, 3.1415/2, 0)
print("downOrientation: ", downOrientation)
pose.orientation.x = downOrientation[0]
pose.orientation.y = downOrientation[1]
pose.orientation.z = downOrientation[2]
pose.orientation.w = downOrientation[3]

pose_B = pose

arm_group.set_pose_target(pose_B)
plan = arm_group.plan()
# print(plan)


time_from_start = plan.joint_trajectory.points[-1].time_from_start.secs + plan.joint_trajectory.points[-1].time_from_start.nsecs / 100000000.0

print("Planner Time to point B: ", time_from_start)
start_time = time.time()
arm_group.go(wait=True)
print("End point")

elapsed_time = time.time() - start_time
print("Elapsed time w/o obstacle: " + str(elapsed_time))

# Adding obstacle
p = PoseStamped()
p.header.frame_id = robot.get_planning_frame()
p.header.stamp = rospy.Time.now()

p.pose.position.x = 0.85
p.pose.position.y = 0.0
p.pose.position.z = 0.70

q = tf.transformations.quaternion_from_euler(0.0, 0.0, numpy.deg2rad(90.0))
p.pose.orientation = Quaternion(*q)

scene.add_box("obstacle", p, (0.05, 1, 1))


# Start point
pose.position.x = 0.4
pose.position.y = -0.2
pose.position.z = 1

downOrientation = tf.transformations.quaternion_from_euler(0, 3.1415/2, 0)
print("downOrientation: ", downOrientation)
pose.orientation.x = downOrientation[0]
pose.orientation.y = downOrientation[1]
pose.orientation.z = downOrientation[2]
pose.orientation.w = downOrientation[3]

pose_A = pose

arm_group.set_pose_target(pose_A)
arm_group.go(wait=True)
print("Start point")

# End point
pose.position.x = 0.4
pose.position.y = 0.2
pose.position.z = 1

downOrientation = tf.transformations.quaternion_from_euler(0, 3.1415/2, 0)
print("downOrientation: ", downOrientation)
pose.orientation.x = downOrientation[0]
pose.orientation.y = downOrientation[1]
pose.orientation.z = downOrientation[2]
pose.orientation.w = downOrientation[3]

pose_B = pose

arm_group.set_pose_target(pose_B)
plan = arm_group.plan()

time_from_start = plan.joint_trajectory.points[-1].time_from_start.secs + plan.joint_trajectory.points[-1].time_from_start.nsecs / 100000000.0

print("Planner Time to point B: ", time_from_start)
start_time = time.time()
arm_group.go(wait=True)
print("End point")

elapsed_time = time.time() - start_time
print("Elapsed time w/ obstacle: " + str(elapsed_time))

arm_group.go(wait=True)
print("End point")

scene.remove_world_object("obstacle")
