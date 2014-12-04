add_executable(image_resizer image_resizer)
target_link_libraries(image_resizer ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(image_splitter image_splitter)
target_link_libraries(image_splitter ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(create_training_data create_training_data)
target_link_libraries(create_training_data ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(visualize_conv_net visualize_conv_net)
target_link_libraries(visualize_conv_net ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES} ${TAO_LIBRARY} ${UNDVC_COMMON_LIBRARY})
