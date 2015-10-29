CREATE TABLE IF NOT EXISTS `tblSplitImages` (
	`splitImageId` int(11) NOT NULL AUTO_INCREMENT,
	`imageId` int(11) NOT NULL,
	`top` int(4) NOT NULL,
	`left` int(4) NOT NULL,
	`width` int(4) NOT NULL,
	`height` int(4) NOT NULL,

	PRIMARY KEY (`splitImageId`),
	INDEX (`imageId`),

	FOREIGN KEY (`imageId`)
		REFERENCES tblImages(`imageId`)
);

CREATE TABLE IF NOT EXISTS `tblSpecies` (
	`speciesId` int(11) NOT NULL AUTO_INCREMENT,
	`name` varchar(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS `tblObjects` (
	`objectId` int(11) NOT NULL AUTO_INCREMENT,
	`speciesId` int(11) NOT NULL,
	`splitImageId` int(11) NOT NULL,
	`top` int(4) NOT NULL,
	`left` int(4) NOT NULL,
	`width` int(4) NOT NULL,
	`height` int(4) NOT NULL,
	`count` int(4) DEFAULT 1,
	`confirmed` tinyint(1) DEFAULT 0,

	PRIMARY KEY (`objectId`),
	INDEX(`speciesId`),
	INDEX(`splitImageId`),

	FOREIGN KEY (`speciesId`)
		REFERENCES tblSpecies(`speciesId`),

	FOREIGN KEY (`splitImageId`)
		REFERENCES tblSplitImages(`splitImageId`)
);