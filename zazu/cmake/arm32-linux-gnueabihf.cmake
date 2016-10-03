# the name of the target operating system
SET( CMAKE_SYSTEM_NAME Linux )
#SET( CMAKE_SYSTEM_PROCESSOR "armv8-a" )
SET( CMAKE_CROSSCOMPILING TRUE )

# Set toolchain path
SET(ROOTPATH    ${ZAZU_TOOL_PATH}/gcc-linaro-arm-linux-gnueabihf/4.9/arm-linux-gnueabihf)

SET(CROSSFIX        arm-linux-gnueabihf-)

# which compilers to use for C and C++
SET(CMAKE_C_COMPILER       ${ROOTPATH}/bin/${CROSSFIX}gcc)
SET(CMAKE_CXX_COMPILER     ${ROOTPATH}/bin/${CROSSFIX}g++)
SET(CMAKE_ASM_COMPILER     ${ROOTPATH}/bin/${CROSSFIX}as)

# here is the target environment located
SET(CMAKE_FIND_ROOT_PATH ${ROOTPATH} ${ROOTPATH}/sysroot)
SET(CMAKE_PREFIX_PATH ${ROOTPATH} ${ROOTPATH}/sysroot)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE BOTH)

SET(SYSLIBS log)

