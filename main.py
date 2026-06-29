def main():
    print("Hello from multi-agent-personal-assistant!")


if __name__ == "__main__":
    main()
from core.memory import init_db, save_history, load_history, clear_history
from core.orchestrator import Orchestrator


def get_agent_key(orch, agent) -> str:
    return next(k for k, v in orch.agents.items() if v == agent)


def main():
    init_db()
    orch = Orchestrator()

    for name, agent in orch.agents.items():
        agent.history = load_history(name)

    print("\n🤖 Multi-Agent Personal Assistant")
    print("=" * 45)
    print("Commands: /email  /research  /calendar  /travel  /reset  /quit")
    print("Or just type freely — auto-routing is on.\n")

    current_agent = None

    while True:
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            break

        if not user_input:
            continue

        if user_input == "/quit":
            for name, agent in orch.agents.items():
                save_history(name, agent.history)
            print("All conversations saved. Goodbye!")
            break

        elif user_input == "/reset":
            if current_agent:
                key = get_agent_key(orch, current_agent)
                current_agent.reset()
                clear_history(key)
                print(f"{current_agent.name} memory cleared.")
            else:
                print("No active agent. Use /email, /research, /calendar, or /travel first.")

        elif user_input.startswith("/"):
            name = user_input[1:]
            if name in orch.agents:
                current_agent = orch.agents[name]
                print(f"Switched to {current_agent.name} ({current_agent.provider})")
            else:
                print("Unknown command. Try /email /research /calendar /travel /reset /quit")

        else:
            if current_agent:
                reply = current_agent.chat(user_input)
                save_history(get_agent_key(orch, current_agent), current_agent.history)
                print(f"\n{current_agent.name}: {reply}\n")
            else:
                current_agent, reply, reason = orch.route(user_input)
                save_history(get_agent_key(orch, current_agent), current_agent.history)
                print(f"\n[Routed to {current_agent.name} — {reason}]")
                print(f"\n{current_agent.name}: {reply}\n")


if __name__ == "__main__":
    main()