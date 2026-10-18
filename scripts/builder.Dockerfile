# syntax=docker/dockerfile:1
FROM archlinux:base@sha256:3c64b538588416593f69a1aebd2f2ec0f2541b29159f32556fa7def2167147a0
# Optional public CA for managed HTTPS proxies. Normal builds need no extra CA.
RUN --mount=type=secret,id=build_ca \
    if [ -s /run/secrets/build_ca ]; then \
      cp /run/secrets/build_ca /etc/ca-certificates/trust-source/anchors/9b7-build-proxy.crt; \
      update-ca-trust; \
    fi; \
    pacman -Syu --noconfirm --needed archiso base-devel sudo git python python-pip \
    python-yaml python-build python-installer python-wheel python-setuptools \
    librsvg shellcheck jq curl rsync qemu-system-x86 edk2-ovmf \
    && pacman -Scc --noconfirm
WORKDIR /project
CMD ["bash"]
