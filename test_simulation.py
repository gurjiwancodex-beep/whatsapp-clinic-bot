"""
Interactive CLI Simulation for WhatsApp Clinic Bot.
Use this script to test conversations and appointment bookings immediately
even before configuring WhatsApp credentials!
"""
import asyncio
import sys
import ai_service
import database
import config

async def run_cli_chat():
    test_patient_phone = "919876543210"
    print("\n" + "="*60)
    print(f"🏥 Welcome to {config.CLINIC_NAME} - WhatsApp AI Bot Simulator")
    print("="*60)
    print("💡 You can type in Punjabi ('Doctor saab nu milna si', 'kal 4 vaje appointment deyo'),")
    print("   Hindi, or English.")
    print("Type 'exit' or 'quit' to end the test.\n")

    if not config.GEMINI_API_KEY:
        print("⚠️ NOTE: GEMINI_API_KEY is not set in .env yet.")
        print("Please paste your free Gemini API key from https://aistudio.google.com/ into .env to talk to the AI.\n")

    while True:
        try:
            user_input = input("\n👤 Patient: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting simulator. Have a great day!")
                break

            print("\n🤖 Bot is typing...")
            # Save user input to DB
            database.save_message(sender_id=test_patient_phone, role="user", message=user_input)
            
            # Generate AI response
            reply = await ai_service.generate_bot_reply(
                sender_id=test_patient_phone,
                incoming_text=user_input
            )
            
            # Save AI response to DB
            database.save_message(sender_id=test_patient_phone, role="model", message=reply)
            
            print(f"🤖 Bot:\n{reply}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting simulator.")
            break

if __name__ == "__main__":
    asyncio.run(run_cli_chat())
