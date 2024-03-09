"""
All pet related functions and resources.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from collections import defaultdict
from functools import lru_cache
from typing import Dict, Union, List

from ruamel.yaml.scalarfloat import ScalarFloat

from .local_data import load_db
from .errors import GSAConfigurationError

logger = logging.getLogger("GSA")

PET_CAGE_ID = 82800


def check_pet_validity(*,
                       pet: Dict
                       ) -> None:
    """
    Verify all the expected components of a pet shopping item are present.

    :param pet: The pet dictionary object.
    """

    if 'budget' not in pet:
        raise GSAConfigurationError(f"Missing a budget.")

    if type(pet['budget']) not in (int, float, ScalarFloat):
        raise GSAConfigurationError(f"Budget is not valid (int/float).")

    if 'species_id' not in pet:
        raise GSAConfigurationError(f"Missing an species_id.")

    if not isinstance(pet['species_id'], int):
        raise GSAConfigurationError(f"Missing a valid species_id (no decimals).")

    if 'rare' in pet and not isinstance(pet['rare'], bool):
        raise GSAConfigurationError("Rare must be provided as a boolean, eg. True or False.")

    if 'level' in pet and not isinstance(pet['level'], int):
        raise GSAConfigurationError("Level must be provided as a integer (no decimals).")

    if 'quality' in pet:
        if not isinstance(pet['quality'], str):
            raise GSAConfigurationError("Quality must be a string (eg. Rare).")

        if pet['quality'].upper() not in ("POOR", "COMMON", "UNCOMMON", "RARE"):
            raise GSAConfigurationError("Quality must be Poor, Common, Uncommon, or Rare.")


@lru_cache
def load_pet_species_db(*,
                        index_by_value: bool = False
                        ) -> Union[dict, defaultdict]:
    """
    A cached method to return a dictionary containing all Battle Pets in World of Warcraft.

    :param index_by_value: Set TRUE if dictionary key should be pet name rather than id.
    """

    pets = load_db(db="pet_species.json")

    if index_by_value:
        named_pets = defaultdict(list)
        for pet in pets:
            named_pets[pets[pet].upper()].append(int(pet))

        pets = named_pets

    logger.debug(f"{len(pets)} pets loaded.")
    return pets


@lru_cache
def load_pet_quality_db(*,
                        index_by_value: bool = False
                        ) -> Union[dict, defaultdict]:
    """
    A cached method to return a dictionary containing all Battle Pet Qualities in World of Warcraft.

    :param index_by_value: Set TRUE if dictionary key should be pet name rather than id.
    """

    qualities = load_db(db="pet_quality.json")

    if index_by_value:
        named_qualities = defaultdict(list)
        for quality in qualities:
            named_qualities[qualities[quality].upper()].append(int(quality))

        qualities = named_qualities

    logger.debug(f"{len(qualities)} pet qualities loaded.")
    return qualities


@lru_cache
def load_pet_breed_db(*,
                      index_by_value: bool = False
                      ) -> Union[dict, defaultdict]:
    """
    A cached method to return a dictionary containing all Battle Pet Breeds in World of Warcraft.

    :param index_by_value: Set TRUE if dictionary key should be pet breed rather than id.
    """

    breeds = load_db(db="pet_breeds.json")

    if index_by_value:
        named_breeds = defaultdict(list)
        for breed in breeds:
            named_breeds[breeds[breed].upper()].append(int(breed))

        breeds = named_breeds

    logger.debug(f"{len(breeds)} pet breeds loaded.")
    return breeds


@lru_cache
def get_pet_breed_from_db(*,
                          pet_breed_id: int
                          ) -> str:
    """
    A cached method to check what the breed of a pet breed_id is.

    :param pet_breed_id: The breed id to lookup.
    """

    breeds = load_pet_breed_db()

    return breeds[str(pet_breed_id)]


@lru_cache
def get_pet_breed_id_from_db(*,
                             pet_breed: str
                             ) -> List[int]:
    """
    A cached method to check what a breed's breed_id is.

    :param pet_breed: The breed name to look up.
    """

    breeds = load_pet_breed_db(index_by_value=True)
    breeds = breeds[pet_breed.upper()]

    if len(breeds) == 0:
        raise GSAConfigurationError(f"A pet quality of {pet_breed} was not found.")

    return breeds


@lru_cache
def get_pet_quality_from_db(*,
                            pet_quality_id: int
                            ) -> str:
    """
    A cached method to check what the quality of a pet quality_id is.

    :param pet_quality_id: The quality id to lookup.
    """

    qualities = load_pet_quality_db()

    return qualities[str(pet_quality_id)]


@lru_cache
def get_pet_quality_id_from_db(*,
                               pet_quality: str
                               ) -> List[int]:
    """
    A cached method to check what a quality's quality_id is.

    :param pet_quality: The quality name to look up.
    """

    qualities = load_pet_quality_db(index_by_value=True)
    qualities = qualities[pet_quality.upper()]

    if len(qualities) == 0:
        raise GSAConfigurationError(f"A pet quality of {pet_quality} was not found.")

    return qualities
