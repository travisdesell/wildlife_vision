class Observation:
    """This class is for a single Observation and function to compare
    two Observations together."""

    def __init__(self, user_id, species_id, x, y, width, height, iob_id):
        self.user_id = user_id
        self.s_id = species_id
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.right = self.x + self.width
        self.bottom = self.y + self.height
        self.area = self.width * self.height
        self.iob_id = iob_id

    def area_overlap(self, o):
        """Gets the area overlap between another Observation"""
        x_overlap = max(0, min(self.right, o.right) - max(self.x, o.x))
        y_overlap = max(0, min(self.bottom, o.bottom) - max(self.y, o.y))
        return x_overlap * y_overlap / float(max(self.area, o.area))

    def point_proximity(self, o):
        """Gets the farthest proximity of a corner to another Observation"""
        left = self.x - o.x
        right = self.right - o.right
        top = self.y - o.y
        bottom = self.bottom - o.bottom

        left = left * left
        right = right * right
        top = top * top
        bottom = bottom * bottom

        top_left = left + top
        top_right = right + top
        bottom_left = left + bottom
        bottom_right = right + bottom

        farthest = max(top_left, top_right, bottom_left, bottom_right)
        return farthest
