package sura.app.entrypoint.rest;

import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import sura.app.usecase.item.CreateItemUseCase;
import sura.app.usecase.item.ListItemsUseCase;

@RestController
public class ItemController {

    private final CreateItemUseCase createItemUseCase;
    private final ListItemsUseCase listItemsUseCase;

    public ItemController(CreateItemUseCase createItemUseCase, ListItemsUseCase listItemsUseCase) {
        this.createItemUseCase = createItemUseCase;
        this.listItemsUseCase = listItemsUseCase;
    }

    @GetMapping("/api/items")
    public List<ItemResponse> list() {
        return listItemsUseCase.execute().stream().map(ItemResponse::from).toList();
    }

    @PostMapping("/api/items")
    @ResponseStatus(HttpStatus.CREATED)
    public ItemResponse create(@RequestBody ItemRequest request) {
        return ItemResponse.from(createItemUseCase.execute(request.description()));
    }
}
