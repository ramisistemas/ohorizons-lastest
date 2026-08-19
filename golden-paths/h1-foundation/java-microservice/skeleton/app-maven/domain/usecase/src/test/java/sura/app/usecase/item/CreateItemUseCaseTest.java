package sura.app.usecase.item;

import org.junit.jupiter.api.Test;
import sura.app.domain.item.Item;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class CreateItemUseCaseTest {

    @Test
    void savesItemThroughGateway() {
        ItemGateway gateway = mock(ItemGateway.class);
        when(gateway.save(any(Item.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CreateItemUseCase useCase = new CreateItemUseCase(gateway);
        Item result = useCase.execute("nuevo item");

        assertEquals("nuevo item", result.getDescription());
    }
}
