package sura.app.domain.item;

import java.time.Instant;
import java.util.Objects;

/**
 * Entidad de dominio pura — sin anotaciones de framework, sin dependencias externas.
 * Ejemplo de referencia: reemplazar por el dominio real del servicio.
 */
public class Item {

    private final String id;
    private final String description;
    private final Instant createdAt;

    public Item(String id, String description, Instant createdAt) {
        this.id = Objects.requireNonNull(id, "id no puede ser nulo");
        this.description = Objects.requireNonNull(description, "description no puede ser nulo");
        this.createdAt = Objects.requireNonNull(createdAt, "createdAt no puede ser nulo");
    }

    public String getId() {
        return id;
    }

    public String getDescription() {
        return description;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
