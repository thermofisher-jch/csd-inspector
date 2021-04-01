#We can use the smaller JRE rather than the JDK
FROM openjdk:8-jre-alpine 
 
ARG RELEASE=3.4.1
ENV RELEASE=$RELEASE
 
#Get distribution archive file, unpack it, create mount point for project directory, and expose service port
RUN apk update && apk add --no-cache wget && \
    wget --no-check-certificate https://github.com/OpenRefine/OpenRefine/releases/download/$RELEASE/openrefine-linux-$RELEASE.tar.gz && \
    tar -xzf openrefine-linux-$RELEASE.tar.gz  && \
    rm openrefine-linux-$RELEASE.tar.gz && \
    mkdir -p /mnt/refine/extensions && \
    cd /mnt/refine/extensions && \
    wget http://data.bits.vib.be/hidden/g7dt6RjuUTU421dY2CwrGePGX/vib-bits.zip && \
    unzip vib-bits.zip && \
    rm vib-bits.zip 
VOLUME /mnt/refine
EXPOSE 3333
 
# Set launch command relative to the release version
CMD openrefine-$RELEASE/refine -i 0.0.0.0 -d /mnt/refine

