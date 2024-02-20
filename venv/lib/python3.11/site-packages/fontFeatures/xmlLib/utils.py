
def put_languages(self, root):
    if hasattr(self, "languages") and self.languages:
        lang_string = ",".join(["/".join(x) for x in self.languages])
        root.attrib["languages"] = lang_string


def put_address(self, root):
    if self.address:
        if isinstance(self.address, str):
            root.attrib["address"] = self.address
        else:
            root.attrib["address"] = str("|".join(self.address))
