import pygame
from pygame._sdl2 import controller


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 260
DEADZONE = 3000


def main() -> None:
    pygame.init()
    pygame.display.set_caption("plaiiboy controller test")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    font = pygame.font.Font(None, 30)
    small_font = pygame.font.Font(None, 24)

    controller.init()
    controller.set_eventstate(True)

    if controller.get_count() == 0:
        raise RuntimeError("Kein Controller gefunden.")

    if not controller.is_controller(0):
        raise RuntimeError(
            "Gerät 0 wird nicht als unterstützter Controller erkannt."
        )

    gamepad = controller.Controller(0)
    controller_name = controller.name_forindex(0)

    last_event = "Noch keine Eingabe erkannt."
    running = True
    clock = pygame.time.Clock()

    print("plaiiboy - live input test")
    print("--------------------------")
    print(f"Controller: {controller_name}")
    print("Testfenster geöffnet.")
    print("Zum Beenden Fenster schließen oder Escape drücken.\n")

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                elif event.type == pygame.CONTROLLERBUTTONDOWN:
                    last_event = f"BUTTON DOWN | button={event.button}"
                    print(last_event)

                elif event.type == pygame.CONTROLLERBUTTONUP:
                    last_event = f"BUTTON UP | button={event.button}"
                    print(last_event)

                elif event.type == pygame.CONTROLLERAXISMOTION:
                    if abs(event.value) > DEADZONE:
                        last_event = (
                            f"AXIS | axis={event.axis} | value={event.value}"
                        )
                        print(last_event)

                elif event.type in (
                    pygame.CONTROLLERTOUCHPADDOWN,
                    pygame.CONTROLLERTOUCHPADMOTION,
                    pygame.CONTROLLERTOUCHPADUP,
                ):
                    last_event = (
                        f"{pygame.event.event_name(event.type)} | {event}"
                    )
                    print(last_event)

                elif event.type == pygame.CONTROLLERDEVICEREMOVED:
                    last_event = "Controller wurde getrennt."
                    print(last_event)

            screen.fill((25, 25, 30))

            title = font.render(
                "plaiiboy – Controller-Test",
                True,
                (240, 240, 240),
            )
            name_text = small_font.render(
                f"Controller: {controller_name}",
                True,
                (220, 220, 220),
            )
            event_text = small_font.render(
                last_event,
                True,
                (220, 220, 220),
            )
            help_text = small_font.render(
                "Tasten drücken oder Sticks bewegen – Escape beendet.",
                True,
                (180, 180, 180),
            )

            screen.blit(title, (30, 30))
            screen.blit(name_text, (30, 90))
            screen.blit(event_text, (30, 135))
            screen.blit(help_text, (30, 190))

            pygame.display.flip()
            clock.tick(60)

    finally:
        gamepad.quit()
        controller.quit()
        pygame.quit()


if __name__ == "__main__":
    main()