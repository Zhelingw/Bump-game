-- ensuring that tables are not duplicated 
drop table if exists Summary;
drop table if exists Player;
drop table if exists Levels;

-- creating the tables for Levels, Player, and Summary
create table Levels(
    ID int, 
    Description text, 
    PRIMARY KEY (ID)
);

create table Player(
    ID int,
    UserName text, 
    PassWord text,
    PRIMARY KEY (ID)
);

create table Summary(
    PlayerID int,
    Level int, 
    TimesPlayed int,
    WinCount int, 
    TieCount int, 
    FOREIGN KEY (PlayerID) REFERENCES Player(ID), 
    FOREIGN KEY (Level) REFERENCES Levels(ID), 
    PRIMARY KEY (PlayerID, Level)
);

-- defining the respective ID and level descriptions to avoid errors later on 
insert into Levels values
    (1, "Easy"), 
    (2, "Moderate"), 
    (3, "Hard");