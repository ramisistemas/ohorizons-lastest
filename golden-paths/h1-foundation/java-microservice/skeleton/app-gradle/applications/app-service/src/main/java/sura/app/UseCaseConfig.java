package sura.app;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import sura.app.usecase.item.CreateItemUseCase;
import sura.app.usecase.item.ItemGateway;
import sura.app.usecase.item.ListItemsUseCase;

/**
 * Los casos de uso son POJOs puros (sin anotaciones de Spring) para mantener
 * el módulo domain-usecase libre de dependencias de framework. Se registran
 * como beans acá, en la capa de aplicación.
 */
@Configuration
public class UseCaseConfig {

    @Bean
    public CreateItemUseCase createItemUseCase(ItemGateway itemGateway) {
        return new CreateItemUseCase(itemGateway);
    }

    @Bean
    public ListItemsUseCase listItemsUseCase(ItemGateway itemGateway) {
        return new ListItemsUseCase(itemGateway);
    }
}
