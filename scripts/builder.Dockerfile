FROM archlinux:base@sha256:3c64b538588416593f69a1aebd2f2ec0f2541b29159f32556fa7def2167147a0
RUN pacman -Syu --noconfirm --needed archiso base-devel sudo git python python-pip \
    python-yaml python-build python-installer python-wheel python-setuptools \
    librsvg shellcheck jq curl qemu-system-x86 edk2-ovmf \
    && pacman -Scc --noconfirm
WORKDIR /project
CMD ["bash"]
