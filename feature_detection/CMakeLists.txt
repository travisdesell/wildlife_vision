add_executable(surf_test surf_test)
target_link_libraries(surf_test ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})

add_executable(surf_flann surf_flann)
target_link_libraries(surf_flann ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${OpenCV_LIBRARIES})
