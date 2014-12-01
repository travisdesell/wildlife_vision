add_executable(canny_edge canny_edge)
target_link_libraries(canny_edge ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(color_histogram_line color_histogram_line dynamic_time_warping)
target_link_libraries(color_histogram_line ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(spiral_histogram spiral_histogram dynamic_time_warping)
target_link_libraries(spiral_histogram ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})
