find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_OPENLST gnuradio-openlst)

FIND_PATH(
    GR_OPENLST_INCLUDE_DIRS
    NAMES gnuradio/openlst/api.h
    HINTS $ENV{OPENLST_DIR}/include
        ${PC_OPENLST_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_OPENLST_LIBRARIES
    NAMES gnuradio-openlst
    HINTS $ENV{OPENLST_DIR}/lib
        ${PC_OPENLST_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-openlstTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_OPENLST DEFAULT_MSG GR_OPENLST_LIBRARIES GR_OPENLST_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_OPENLST_LIBRARIES GR_OPENLST_INCLUDE_DIRS)
