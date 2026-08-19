# syntax=docker/dockerfile:1

# --- Build stage ---
FROM maven:3.9.9-eclipse-temurin-21-alpine AS builder
WORKDIR /build
COPY . .
RUN mvn -q -pl applications/app-service -am package -DskipTests

# --- Runtime stage ---
FROM eclipse-temurin:21-jre-alpine
ARG APP_VERSION=0.1.0
ENV TZ="America/Bogota"

RUN addgroup -S app && adduser -S app -G app
WORKDIR /opt/app

COPY --from=builder --chown=app:app /build/applications/app-service/target/applications-app-service-${APP_VERSION}.jar app.jar

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health/liveness || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
