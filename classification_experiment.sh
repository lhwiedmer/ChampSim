conda create -n dev_cpp cmake pkg-config ninja -c conda-forge
conda activate dev_cpp

git submodule update --init
vcpkg/bootstrap-vcpkg.sh
vcpkg/vcpkg install