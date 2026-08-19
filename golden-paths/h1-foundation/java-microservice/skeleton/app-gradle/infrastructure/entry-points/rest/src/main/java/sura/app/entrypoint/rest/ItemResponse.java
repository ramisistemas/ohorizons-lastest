package sura.app.entrypoint.rest;

import java.time.Instant;
import sura.app.domain.item.Item;

public record ItemResponse(String id, String description, Instant createdAt) {

    public static ItemResponse from(Item item) {
        return new ItemResponse(item.getId(), item.getDescription(), item.getCreatedAt());
    }
}
