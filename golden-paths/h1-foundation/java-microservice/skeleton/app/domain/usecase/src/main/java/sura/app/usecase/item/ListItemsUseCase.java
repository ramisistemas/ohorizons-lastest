package sura.app.usecase.item;

import java.util.List;
import sura.app.domain.item.Item;

public class ListItemsUseCase {

    private final ItemGateway itemGateway;

    public ListItemsUseCase(ItemGateway itemGateway) {
        this.itemGateway = itemGateway;
    }

    public List<Item> execute() {
        return itemGateway.findAll();
    }
}
