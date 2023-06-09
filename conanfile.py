import os.path
from conan import ConanFile
import conan.tools.files
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conans.errors import ConanInvalidConfiguration
from conan.tools.microsoft import unix_path
from conan.tools.microsoft.visual import is_msvc_static_runtime


class OPENCVConan(ConanFile):
    name = "opencv"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    generators = "CMakeDeps"

    def validate(self):
        if self.settings.os == "Android":
            if int(str(self.settings.os.api_level)) < 24:
                # https://github.com/opencv/opencv/blob/4.5.5/modules/videoio/cmake/detect_android_camera.cmake
                raise ConanInvalidConfiguration("opencv videoio on Android requires abi level >= 24")

    def requirements(self):
        self.requires(f"eigen/{self.version}")
        self.requires(f"zlib/{self.version}")
        self.requires(f"libspng/{self.version}")
        self.requires(f"libjpeg_turbo/{self.version}")

    def layout(self):
        cmake_layout(self)


    def export_sources(self):
        conan.tools.files.copy(self, "*", self.recipe_folder, self.export_sources_folder)
        conan.tools.files.copy(self, "*", os.path.join(self.recipe_folder, "..", "opencv_contrib"), os.path.join(self.export_sources_folder, "opencv_contrib"))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables['BUILD_LIST'] = "core,features2d,imgcodecs,imgproc,highgui,video,videoio,calib3d,aruco,xfeatures2d"

        tc.variables['CMAKE_INSTALL_RPATH_USE_LINK_PATH'] = False
        tc.variables['OPENCV_EXTRA_MODULES_PATH'] = unix_path(self, os.path.join(self.source_folder,
                                                                                 "./opencv_contrib/modules")).replace(
            os.sep, '/')
        if self.settings.compiler == "msvc":
            tc.variables['BUILD_WITH_STATIC_CRT'] = is_msvc_static_runtime(self)
        tc.variables['BUILD_TESTS'] = "OFF"
        tc.variables['BUILD_PERF_TESTS'] = "OFF"
        tc.variables['BUILD_EXAMPLES'] = "OFF"
        tc.variables['BUILD_PACKAGE'] = "OFF"
        tc.variables['BUILD_opencv_apps'] = "OFF"
        tc.variables['BUILD_JAVA'] = "OFF"
        tc.variables['BUILD_opencv_python2'] = "OFF"
        tc.variables['BUILD_opencv_python3'] = "OFF"

        tc.variables['WITH_SPNG'] = "ON"
        tc.variables['WITH_OPENJPEG'] = "OFF"
        tc.variables['WITH_JASPER'] = "OFF"
        tc.variables['WITH_JPEG'] = "ON"

        tc.variables['WITH_ADE'] = "OFF"
        tc.variables['WITH_PROTOBUF'] = "OFF"
        tc.variables['WITH_PNG'] = "OFF"
        tc.variables['WITH_TIFF'] = "OFF"
        tc.variables['WITH_OPENEXR'] = "OFF"
        tc.variables['WITH_WEBP'] = "OFF"
        tc.variables['WITH_FFMPEG'] = "OFF"

        tc.variables['BUILD_ZLIB'] = "OFF"
        tc.variables['BUILD_JPEG'] = "OFF"

        tc.variables['WITH_IPP'] = self.settings.os in ["Windows", "Linux"]

        if self.settings.os == "Emscripten":
            tc.variables['WITH_ITT'] = "OFF"
            tc.variables['WITH_QUIRC'] = "OFF"
            tc.variables['WITH_ADE'] = "OFF"
            tc.variables['BUILD_opencv_js'] = "OFF"
            tc.variables['CPU_BASELINE'] = ""
            tc.variables['CPU_DISPATCH'] = ""
            tc.variables['CV_ENABLE_INTRINSICS'] = self.settings.os.simd
            tc.variables['BUILD_WASM_INTRIN_TESTS'] = "OFF"

            # emsdk 3.1.31 puts version definition in <emscripten/version.h>, which isn't included by default
            version_parts = str(self.settings.os.sdk_version).split(".")
            tc.preprocessor_definitions["__EMSCRIPTEN_major__"] = version_parts[0]
            tc.preprocessor_definitions["__EMSCRIPTEN_minor__"] = version_parts[1]
            tc.preprocessor_definitions["__EMSCRIPTEN_tiny__"] = version_parts[2]

        if self.settings.os == "Android":
            tc.variables['BUILD_ANDROID_EXAMPLES'] = "OFF"

        if self.settings.os == "iOS":
            tc.variables['IOS'] = 1
            tc.variables['WITH_OPENCL'] = "OFF"
            tc.variables['APPLE_FRAMEWORK'] = "OFF"
            tc.variables['BUILD_opencv_world'] = "OFF"

        tc.variables['OPENCV_BIN_INSTALL_PATH'] = "bin"
        tc.variables['OPENCV_LIB_INSTALL_PATH'] = "lib"
        tc.variables['OPENCV_LIB_ARCHIVE_INSTALL_PATH'] = "lib"
        tc.variables['OPENCV_3P_LIB_INSTALL_PATH'] = "lib"
        tc.variables['OPENCV_CONFIG_INSTALL_PATH'] = "cmake"
        tc.variables['OPENCV_INCLUDE_INSTALL_PATH'] = "include"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.builddirs.append("cmake")
        self.cpp_info.set_property("cmake_file_name", "OpenCV")
