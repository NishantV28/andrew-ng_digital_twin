import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.memory import (
    add_topic_discussed,
    get_chat_history,
    get_topics_discussed,
    get_user_facts,
    reset_all_memories,
    save_message,
    update_user_fact,
)


class TestMemorySystem(unittest.TestCase):
    def setUp(self):
        reset_all_memories()

    def test_chat_history_returns_latest_messages(self):
        session_id = "test_session"
        for index in range(15):
            save_message(session_id, "user", f"message {index}")

        history = get_chat_history(session_id, limit=5)
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0]["content"], "message 10")
        self.assertEqual(history[-1]["content"], "message 14")

    def test_user_facts_are_session_scoped(self):
        update_user_fact("session_a", "User Name", "Nishant")
        update_user_fact("session_b", "User Name", "Aarav")

        self.assertEqual(get_user_facts("session_a")["User Name"]["value"], "Nishant")
        self.assertEqual(get_user_facts("session_b")["User Name"]["value"], "Aarav")

    def test_topics_are_session_scoped(self):
        add_topic_discussed("session_a", "Gradient Descent", "Hill-climbing analogy")
        add_topic_discussed("session_b", "LDA", "Topic model overview")

        self.assertIn("Gradient Descent", get_topics_discussed("session_a"))
        self.assertNotIn("Gradient Descent", get_topics_discussed("session_b"))


if __name__ == "__main__":
    unittest.main()
