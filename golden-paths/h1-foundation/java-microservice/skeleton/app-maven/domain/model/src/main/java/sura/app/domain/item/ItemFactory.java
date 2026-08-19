package sura.app.domain.item;

import java.time.Instant;
import java.util.UUID;

public final class ItemFactory {

    private ItemFactory() {
    }

    public static Item create(String description) {
        return new Item(UUID.randomUUID().toString(), description, Instant.now());
    }
}
