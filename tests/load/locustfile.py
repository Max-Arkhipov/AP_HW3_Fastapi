from locust import HttpUser, task, between
import random
import string


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Регистрация и авторизация пользователя перед началом тестов"""
        self.username = f"testuser_{random.randint(1, 100000)}"
        self.password = "testpassword"

        self.client.post("/auth/register", json={"username": self.username, "password": self.password})
        # response = self.client.post("/auth/login", json={"username": self.username, "password": self.password})
        response = self.client.post("/auth/login", data={"username": self.username, "password": self.password})
        self.token = response.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(2)
    def create_short_link(self):
        """Создание сокращенной ссылки"""
        original_url = f"https://example.com/{''.join(random.choices(string.ascii_letters, k=10))}"
        response = self.client.post("/links/shorten", json={"original_url": original_url}, headers=self.headers)
        if response.status_code == 200:
            self.short_code = response.json()["short_code"]

    @task(3)
    def get_link_info(self):
        """Получение информации о сокращенной ссылке"""
        if hasattr(self, "short_code"):
            self.client.get(f"/links/get_link/{self.short_code}", headers=self.headers)

    @task(1)
    def delete_short_link(self):
        """Удаление сокращенной ссылки"""
        if hasattr(self, "short_code"):
            response = self.client.delete(f"/links/delete_link/{self.short_code}", headers=self.headers)
            if response.status_code == 200:
                del self.short_code


if __name__ == "__main__":
    import os

    os.system("locust -f locustfile.py --host=http://localhost:8000 -u 10 -r 2 --headless --run-time 1m")
