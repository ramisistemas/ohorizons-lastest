package sura.app.adapter.inmemory;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.stereotype.Component;
import sura.app.domain.item.Item;
import sura.app.usecase.item.ItemGateway;

/**
 * Implementación en memoria del puerto ItemGateway. Sirve para que el golden
 * path sea ejecutable de inmediato, sin depender de una base de datos.
 * Reemplazar por un adaptador real (JPA/R2DBC) cuando el proyecto lo requiera.
 */
@Component
public class InMemoryItemRepositoryAdapter implements ItemGateway {

    private final List<Item> items = new CopyOnWriteArrayList<>();

    @Override
    public Item save(Item item) {
        items.add(item);
        return item;
    }

    @Override
    public List<Item> findAll() {
        return List.copyOf(items);
    }
}
