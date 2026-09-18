import threading
import keyboard

from app.config import STREAM
from core.orchestrator.orchestrator import Orchestrator
from voice.voice_pipeline import run as run_voice


def main():

    orchestrator = Orchestrator()

    print("================================")
    print("        My Personal AI")
    print("================================")
    print("Ctrl+C → Exit application\n")

    # Ctrl+M event
    menu_event = threading.Event()

    keyboard.add_hotkey(
        "ctrl+m",
        menu_event.set
    )

    # =================================
    # MAIN MENU
    # =================================

    while True:

        print("Choose a mode:")
        print("1. Chat with Agent")
        print("2. Talk with Agent")
        print("3. Exit")

        try:
            choice = input("\nSelect: ").strip()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            return

        # =================================
        # CHAT MODE
        # =================================

        if choice == "1":

            print("\n--- Chat Mode ---")
            print("Type 'back' to return to menu.")
            print("Type 'exit' to close the application.\n")

            while True:

                try:
                    user_input = input("You: ").strip()

                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    return

                if user_input.lower() == "back":
                    print()
                    break

                if user_input.lower() == "exit":
                    print("\nGoodbye!")
                    return

                if not user_input:
                    continue

                if user_input.lower() == "history":

                    print("\n---- Current history ----")

                    print(
                        orchestrator.agent.context.get_messages()
                    )

                    print("--------------------------\n")

                    continue

                response = orchestrator.process(user_input)

                if not STREAM:

                    print(f"\nAI: {response}\n")

        # =================================
        # TALK MODE
        # =================================

        elif choice == "2":

            print("\n================================")
            print("         TALK SESSION")
            print("================================")
            print("Speak naturally with Mopi.\n")
            print("Ctrl+C → Exit application   \nCtrl+M → Main menu")
            print("================================\n")

            # ---------------------------------
            # CONTINUOUS TALK SESSION
            # ---------------------------------

            while True:

                try:

                    # Reset Ctrl+M event
                    menu_event.clear()

                    # Start voice pipeline
                    final_text = run_voice(menu_event)

                except KeyboardInterrupt:

                    print("\n\nGoodbye!")
                    return

                # ---------------------------------
                # CTRL + M
                # ---------------------------------

                if final_text == "__BACK_TO_MENU__":

                    print("\n[Returning to menu...]\n")

                    break

                # ---------------------------------
                # NO SPEECH
                # ---------------------------------

                if not final_text:

                    print("\n[No speech detected]\n")
                    continue

                # ---------------------------------
                # VOICE COMMAND → MENU
                # ---------------------------------

                if "back to menu" in final_text.lower():

                    print("\n[Returning to menu...]\n")

                    break

                if final_text.lower() in (
                    "back",
                    "go back",
                    "return to menu",
                ):

                    print("\n[Returning to menu...]\n")

                    break

                # ---------------------------------
                # PROCESS
                # ---------------------------------

                print("\n[Processing...]\n")

                response = orchestrator.process(
                    final_text
                )

                # ---------------------------------
                # AI RESPONSE
                # ---------------------------------

                if not STREAM:

                    print(
                        f"[AI] {response}\n"
                    )

                # IMPORTANT:
                # Do NOT print [Listening...] here.
                #
                # voice_pipeline.py already prints it
                # when the next listening cycle starts.

        # =================================
        # EXIT
        # =================================

        elif choice == "3":

            print("\nGoodbye!")
            break

        # =================================
        # INVALID OPTION
        # =================================

        else:

            print(
                "\nInvalid choice. "
                "Please select 1, 2, or 3.\n"
            )


# =================================
# ENTRY POINT
# =================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("\n\nGoodbye!")