package sura.app.domain.item;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class ItemFactoryTest {

    @Test
    void createsItemWithGeneratedIdAndTimestamp() {
        Item item = ItemFactory.create("primer item");

        assertNotNull(item.getId());
        assertNotNull(item.getCreatedAt());
        assertEquals("primer item", item.getDescription());
    }
}
