from config.testing import APITestCase


class LibraryAPITests(APITestCase):
    def test_list_filter_and_search(self):
        data = self.get("/library/resources").json()
        self.assertEqual(len(data), 2)
        self.assertEqual(
            data[0]["roadmaps"], [{"id": self.roadmap.pk, "name": "Quant path"}]
        )
        self.assertEqual(
            [r["title"] for r in self.get("/library/resources?kind=video").json()],
            ["Lecture video"],
        )
        self.assertEqual(len(self.get("/library/resources?q=blitz").json()), 1)
        self.assertEqual(
            [k["value"] for k in self.get("/library/kinds").json()], ["book", "video"]
        )

    def test_detail(self):
        data = self.get(f"/library/resources/{self.video.pk}").json()
        self.assertEqual(data["resource"]["kind_label"], "Video")
        self.assertFalse(data["resource"]["is_pdf"])
        self.assertEqual(data["topics"][0]["id"], self.b.pk)
        self.assertEqual(data["topics"][0]["week"], 1)
        self.assertEqual(data["placements"][0]["roadmap"]["id"], self.roadmap.pk)
        book = self.get(f"/library/resources/{self.book.pk}").json()
        self.assertTrue(book["resource"]["is_pdf"])
        self.assertEqual(
            book["courses"], [{"id": self.course.pk, "name": "Probability"}]
        )
        self.assertEqual(self.get("/library/resources/999").status_code, 404)
