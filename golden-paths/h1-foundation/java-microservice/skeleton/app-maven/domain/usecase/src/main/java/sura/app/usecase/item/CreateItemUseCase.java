package sura.app.usecase.item;

import sura.app.domain.item.Item;
import sura.app.domain.item.ItemFactory;

public class CreateItemUseCase {

    private final ItemGateway itemGateway;

    public CreateItemUseCase(ItemGateway itemGateway) {
        this.itemGateway = itemGateway;
    }

    public Item execute(String description) {
        Item item = ItemFactory.create(description);
        return itemGateway.save(item);
    }
}
