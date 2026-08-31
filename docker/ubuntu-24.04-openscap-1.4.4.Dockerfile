FROM ubuntu@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517

ARG OPENSCAP_VERSION=1.4.4
ARG OPENSCAP_SHA256=25b1b046822121204e6d53d877a532c88bf7fde14b94c9c72297cd5709b03478

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates curl build-essential cmake pkg-config libbz2-dev \
        libxml2-dev libxslt1-dev libxmlsec1-dev libxmlsec1-openssl libcurl4-openssl-dev \
        libssl-dev libpcre2-dev libacl1-dev libcap-dev libgcrypt20-dev libblkid-dev \
        libselinux1-dev libdbus-1-dev libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN curl --fail --location --retry 3 --output openscap.tar.gz \
        "https://github.com/OpenSCAP/openscap/releases/download/${OPENSCAP_VERSION}/openscap-${OPENSCAP_VERSION}.tar.gz" \
    && echo "${OPENSCAP_SHA256}  openscap.tar.gz" | sha256sum --check --strict \
    && tar -xzf openscap.tar.gz \
    && cmake -S "openscap-${OPENSCAP_VERSION}" -B build -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_TESTS=OFF -DENABLE_DOCS=OFF -DENABLE_SCE=OFF -DENABLE_PYTHON3=OFF -DENABLE_PERL=OFF \
        -DENABLE_OSCAP_UTIL_DOCKER=OFF -DENABLE_OSCAP_UTIL_AS_RPM=OFF \
        -DENABLE_OSCAP_UTIL_SSH=OFF -DENABLE_OSCAP_UTIL_VM=OFF \
        -DENABLE_OSCAP_UTIL_PODMAN=OFF -DENABLE_OSCAP_UTIL_IM=OFF \
        -DENABLE_OSCAP_UTIL_CHROOT=OFF \
    && cmake --build build --target oscap --parallel 2 \
    && cmake --install build \
    && ldconfig \
    && oscap --version

ENTRYPOINT ["oscap"]
