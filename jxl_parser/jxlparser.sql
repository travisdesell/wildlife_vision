CREATE TABLE IF NOT EXISTS `tblFlights` (
	`flightId` int(11) NOT NULL AUTO_INCREMENT,
	`timestamp` DATETIME NOT NULL,
	`name` varchar(16) NOT NULL,
	`latitude` float(7, 4) NOT NULL,
	`longitude` float(7, 4) NOT NULL,
	`height` float(7, 4) NOT NULL,
	`yaw` float(7, 4) NOT NULL,
	`pitch` float(7, 4) NOT NULL,
	`roll` float(7, 4) NOT NULL,
	`img_height` int(11) NOT NULL,
	`img_width` int(11) NOT NULL,

	PRIMARY KEY (`flightId`)
);

CREATE TABLE IF NOT EXISTS `tblImages` (
	`imageId` int(11) NOT NULL AUTO_INCREMENT,
	`flightId` int(11) NOT NULL,
	`timestamp` DATETIME NOT NULL,
	`name` varchar(16) NOT NULL,
	`latitude` float(7, 4) NOT NULL,
	`longitude` float(7, 4) NOT NULL,
	`height` float(7, 4) NOT NULL,
	`yaw` float(7, 4) NOT NULL,
	`pitch` float(7, 4) NOT NULL,
	`roll` float(7, 4) NOT NULL,
	`img_height` int(11) NOT NULL,
	`img_width` int(11) NOT NULL,

	PRIMARY KEY (`imageId`),
	INDEX (`flightId`),

	FOREIGN KEY (`flightId`)
		REFERENCES tblFlights(`flightId`)
);