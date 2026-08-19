# syntax=docker/dockerfile:1

# --- Build stage ---
FROM gradle:8.10.2-jdk21-alpine AS builder
WORKDIR /build
COPY . .
RUN gradle :applications-app-service:bootJar --no-daemon

# --- Runtime stage ---
FROM eclipse-temurin:21-jre-alpine
ARG APP_VERSION=0.1.0
ENV TZ="America/Bogota"

RUN addgroup -S app && adduser -S app -G app
WORKDIR /opt/app

COPY --from=builder --chown=app:app /build/applications/app-service/build/libs/applications-app-service-${APP_VERSION}.jar app.jar

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health/liveness || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
