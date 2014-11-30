add_executable(vision_nn vision_nn)
target_link_libraries(vision_nn ${MPI_LIBRARY} ${MPI_EXTRA_LIBRARY} ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${TAO_LIBRARY} ${UNDVC_COMMON_LIBRARY})

add_executable(conv_nn conv_nn)
target_link_libraries(conv_nn ${MPI_LIBRARY} ${MPI_EXTRA_LIBRARY} ${Boost_SYSTEM_LIBRARY} ${Boost_FILESYSTEM_LIBRARY} pthread ${TAO_LIBRARY} ${UNDVC_COMMON_LIBRARY})
