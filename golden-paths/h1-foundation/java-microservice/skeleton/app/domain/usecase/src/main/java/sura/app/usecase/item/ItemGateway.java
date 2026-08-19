package sura.app.usecase.item;

import java.util.List;
import sura.app.domain.item.Item;

/**
 * Puerto de salida (driven port) — la infraestructura provee la implementación real.
 */
public interface ItemGateway {

    Item save(Item item);

    List<Item> findAll();
}
