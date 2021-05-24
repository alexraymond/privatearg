from enum import IntEnum, auto
from base_culture import Culture
from argument import Argument, PrivateArgument, ArgumentationFramework
from boat_agent import BoatAgent
import random


class BoatCategory(IntEnum):
    Civilian = auto()
    Corporate = auto()
    Police = auto()
    CoastGuard = auto()
    Military = auto()


class TaskedStatus(IntEnum):
    AtEase = auto()
    Returning = auto()
    Tasked = auto()


class TaskNature(IntEnum):
    Leisure = auto()
    Sport = auto()
    Trade = auto()
    Training = auto()
    Patrol = auto()
    Pursuit = auto()
    Combat = auto()


class EmergencyNature(IntEnum):
    NoEmergency = auto()
    Mechanical = auto()
    SickPassenger = auto()
    Fire = auto()


class PayloadType(IntEnum):
    Empty = auto()
    Food = auto()
    MedicalSupplies = auto()


class SensitivePayload(IntEnum):
    NoSensitivePayload = auto()
    Weapons = auto()
    WantedPrisoner = auto()


class DiplomaticCredentials(IntEnum):
    NoCredentials = auto()
    Diplomat = auto()
    UnitedNations = auto()


class MilitaryRank(IntEnum):
    NoRank = auto()
    Officer = auto()
    Lieutenant = auto()
    Commander = auto()
    Captain = auto()
    Major = auto()
    Colonel = auto()
    General = auto()
    Admiral = auto()


class VIPIdentity(IntEnum):
    OrdinaryPerson = auto()
    BusinessPerson = auto()
    Celebrity = auto()
    Politician = auto()


class SuperVIP(IntEnum):
    NoSuperVIP = auto()
    PrimeMinister = auto()
    HeadOfState = auto()


class UndercoverOps(IntEnum):
    NoSpy = auto()
    Spy = auto()


class VehicleCost(IntEnum):
    Cheap = auto()
    Reasonable = auto()
    Expensive = auto()
    VeryExpensive = auto()
    WorthMillions = auto()


class VehicleAge(IntEnum):
    BrandNew = auto()
    SlightlyUsed = auto()
    WornDown = auto()
    Old = auto()
    Vintage = auto()

def always_true(*args, **kwargs):
    return True

class BoatCulture(Culture):
    def __init__(self):
        self.ids = {}
        super().__init__()
        self.name = "Boat Culture"
        self.raw_bw_framework = None

        self.properties = {"BoatCategory": BoatCategory.Civilian,
                           "TaskedStatus": TaskedStatus.Returning,
                           "TaskNature": TaskNature.Leisure,
                           "EmergencyNature": EmergencyNature.NoEmergency,
                           "PayloadType": PayloadType.Empty,
                           "SensitivePayload": SensitivePayload.NoSensitivePayload,
                           "DiplomaticCredentials": DiplomaticCredentials.NoCredentials,
                           "MilitaryRank": MilitaryRank.NoRank,
                           "VIPIdentity": VIPIdentity.OrdinaryPerson,
                           "SuperVIP": SuperVIP.NoSuperVIP,
                           "UndercoverOps": UndercoverOps.NoSpy,
                           "VehicleCost": VehicleCost.Cheap,
                           "VehicleAge": VehicleAge.BrandNew}

        self.create_arguments()
        self.define_attacks()
        self.generate_bw_framework()

    def create_arguments(self):
        """
        Defines set of arguments present in the culture and their verifier functions.
        """
        args = []

        _id = 0
        motion = PrivateArgument(arg_id=_id,
                                 hypothesis_text="You should give way to me.",
                                 privacy_cost=0)
        self.ids["motion"] = _id
        motion.hypothesis_verifier = lambda *gen: True  # Motions are always valid.
        args.append(motion)

        ################################################################################

        _id += 1
        higher_category = PrivateArgument(arg_id=_id,
                                          hypothesis_text="I think my category is superior to yours.",
                                          verified_fact_text="My category is provably equal or superior to yours.",
                                          privacy_cost=0)
        self.ids["higher_category"] = _id

        def higher_category_hv(my: BoatAgent, their: BoatAgent):
            return my.BoatCategory > BoatCategory.Civilian

        def higher_category_fv(my: BoatAgent, their: BoatAgent):
            return my.BoatCategory >= their.BoatCategory

        higher_category.hypothesis_verifier = higher_category_hv
        higher_category.fact_verifier = higher_category_fv
        args.append(higher_category)

        ################################################################################

        _id += 1
        tasked_status = PrivateArgument(arg_id=_id,
                                        hypothesis_text="I think my tasked status is more important than yours.",
                                        verified_fact_text="My tasked status is provably equal or superior to yours.",
                                        privacy_cost=3)
        self.ids["tasked_status"] = _id

        def tasked_status_hv(my: BoatAgent, their: BoatAgent):
            return my.TaskedStatus > TaskedStatus.AtEase

        def tasked_status_fv(my: BoatAgent, their: BoatAgent):
            return my.TaskedStatus >= their.TaskedStatus

        tasked_status.hypothesis_verifier = tasked_status_hv
        tasked_status.fact_verifier = tasked_status_fv
        args.append(tasked_status)

        ################################################################################

        _id += 1
        task_nature = PrivateArgument(arg_id=_id,
                                      hypothesis_text="I think the nature of my task is more important than yours.",
                                      verified_fact_text="My task is equal or more important than yours.",
                                      privacy_cost=5)
        self.ids["task_nature"] = _id

        def task_nature_hv(my: BoatAgent, their: BoatAgent):
            return my.TaskNature > TaskNature.Leisure

        def task_nature_fv(my: BoatAgent, their: BoatAgent):
            return my.TaskNature >= their.TaskNature

        task_nature.hypothesis_verifier = task_nature_hv
        task_nature.fact_verifier = task_nature_fv
        args.append(task_nature)

        ################################################################################

        _id += 1
        has_emergency = PrivateArgument(arg_id=_id,
                                        hypothesis_text="I have an emergency on board.",
                                        verified_fact_text="I also have an emergency that is equal or more critical than yours.",
                                        privacy_cost=5)
        self.ids["has_emergency"] = _id

        def has_emergency_hv(my: BoatAgent, their: BoatAgent):
            return my.EmergencyNature > EmergencyNature.NoEmergency

        def has_emergency_fv(my: BoatAgent, their: BoatAgent):
            return my.EmergencyNature >= their.EmergencyNature

        has_emergency.hypothesis_verifier = has_emergency_hv
        has_emergency.fact_verifier = has_emergency_fv
        args.append(has_emergency)

        ################################################################################

        _id += 1
        payload_type = PrivateArgument(arg_id=_id,
                                       hypothesis_text="I have cargo with me.",
                                       verified_fact_text="I also have cargo that is equal or more important than yours.",
                                       privacy_cost=5)
        self.ids["payload_type"] = _id

        def payload_type_hv(my: BoatAgent, their: BoatAgent):
            return my.PayloadType > PayloadType.Empty

        def payload_type_fv(my: BoatAgent, their: BoatAgent):
            return my.PayloadType >= their.PayloadType

        payload_type.hypothesis_verifier = payload_type_hv
        payload_type.fact_verifier = payload_type_fv
        args.append(payload_type)

        ################################################################################

        _id += 1
        sensitive_payload = PrivateArgument(arg_id=_id,
                                            hypothesis_text="I have sensitive cargo with me.",
                                            verified_fact_text="I also have cargo that is equal or more sensitive than yours.",
                                            privacy_cost=15)
        self.ids["sensitive_payload"] = _id

        def sensitive_payload_hv(my: BoatAgent, their: BoatAgent):
            return my.SensitivePayload > SensitivePayload.NoSensitivePayload

        def sensitive_payload_fv(my: BoatAgent, their: BoatAgent):
            return my.SensitivePayload >= their.SensitivePayload

        sensitive_payload.hypothesis_verifier = sensitive_payload_hv
        sensitive_payload.fact_verifier = sensitive_payload_fv
        args.append(sensitive_payload)

        ################################################################################

        _id += 1
        diplomatic_credentials = PrivateArgument(arg_id=_id,
                                                 hypothesis_text="I have diplomatic credentials.",
                                                 verified_fact_text="I have equivalent or superior diplomatic credentials.",
                                                 privacy_cost=15)
        self.ids["diplomatic_credentials"] = _id

        def diplomatic_credentials_hv(my: BoatAgent, their: BoatAgent):
            return my.DiplomaticCredentials > DiplomaticCredentials.NoCredentials

        def diplomatic_credentials_fv(my: BoatAgent, their: BoatAgent):
            return my.DiplomaticCredentials >= their.DiplomaticCredentials

        diplomatic_credentials.hypothesis_verifier = diplomatic_credentials_hv
        diplomatic_credentials.fact_verifier = diplomatic_credentials_fv
        args.append(diplomatic_credentials)

        ################################################################################

        _id += 1
        military_rank = PrivateArgument(arg_id=_id,
                                        hypothesis_text="I believe my Military Rank is higher than yours.",
                                        verified_fact_text="I have equivalent or superior Military Rank.",
                                        privacy_cost=7)
        self.ids["military_rank"] = _id

        def military_rank_hv(my: BoatAgent, their: BoatAgent):
            return my.MilitaryRank > MilitaryRank.NoRank

        def military_rank_fv(my: BoatAgent, their: BoatAgent):
            return my.MilitaryRank >= their.MilitaryRank

        military_rank.hypothesis_verifier = military_rank_hv
        military_rank.fact_verifier = military_rank_fv
        args.append(military_rank)

        ################################################################################

        _id += 1
        vip_identity = PrivateArgument(arg_id=_id,
                                       hypothesis_text="I have an important passenger.",
                                       verified_fact_text="I also have a passenger equally or more important.",
                                       privacy_cost=7)
        self.ids["vip_identity"] = _id

        def vip_identity_hv(my: BoatAgent, their: BoatAgent):
            return my.VIPIdentity > VIPIdentity.OrdinaryPerson

        def vip_identity_fv(my: BoatAgent, their: BoatAgent):
            return my.VIPIdentity >= their.VIPIdentity

        vip_identity.hypothesis_verifier = vip_identity_hv
        vip_identity.fact_verifier = vip_identity_fv
        args.append(vip_identity)

        ################################################################################

        _id += 1
        super_vip = PrivateArgument(arg_id=_id,
                                    hypothesis_text="I have a super important passenger.",
                                    verified_fact_text="I also have a passenger equally or more important.",
                                    privacy_cost=20)
        self.ids["super_vip"] = _id

        def super_vip_hv(my: BoatAgent, their: BoatAgent):
            return my.SuperVIP > SuperVIP.NoSuperVIP

        def super_vip_fv(my: BoatAgent, their: BoatAgent):
            return my.SuperVIP >= their.SuperVIP

        super_vip.hypothesis_verifier = super_vip_hv
        super_vip.fact_verifier = super_vip_fv
        args.append(super_vip)

        ################################################################################

        _id += 1
        undercover_ops = PrivateArgument(arg_id=_id,
                                         hypothesis_text="I am a spy.",
                                         verified_fact_text="I am also a spy.",
                                         privacy_cost=30)
        self.ids["undercover_ops"] = _id

        def undercover_ops_hv(my: BoatAgent, their: BoatAgent):
            return my.UndercoverOps > UndercoverOps.NoSpy

        def undercover_ops_fv(my: BoatAgent, their: BoatAgent):
            return my.UndercoverOps >= their.UndercoverOps

        undercover_ops.hypothesis_verifier = undercover_ops_hv
        undercover_ops.fact_verifier = undercover_ops_fv
        args.append(undercover_ops)

        ################################################################################

        _id += 1
        vehicle_cost = PrivateArgument(arg_id=_id,
                                       hypothesis_text="I believe I paid more for my vehicle than you.",
                                       verified_fact_text="My vehicle cost at least the same as yours, or more.",
                                       privacy_cost=10)
        self.ids["vehicle_cost"] = _id

        def vehicle_cost_hv(my: BoatAgent, their: BoatAgent):
            return my.VehicleCost > VehicleCost.Cheap

        def vehicle_cost_fv(my: BoatAgent, their: BoatAgent):
            return my.VehicleCost >= their.VehicleCost

        vehicle_cost.hypothesis_verifier = vehicle_cost_hv
        vehicle_cost.fact_verifier = vehicle_cost_fv
        args.append(vehicle_cost)

        ################################################################################

        _id += 1
        vehicle_age = PrivateArgument(arg_id=_id,
                                      hypothesis_text="I believe my vehicle is older than yours.",
                                      verified_fact_text="My vehicle is at least as old as yours, or more.",
                                      privacy_cost=4)
        self.ids["vehicle_age"] = _id

        def vehicle_age_hv(my: BoatAgent, their: BoatAgent):
            return my.VehicleAge > VehicleAge.BrandNew

        def vehicle_age_fv(my: BoatAgent, their: BoatAgent):
            return my.VehicleAge >= their.VehicleAge

        vehicle_age.hypothesis_verifier = vehicle_age_hv
        vehicle_age.fact_verifier = vehicle_age_fv
        args.append(vehicle_age)

        self.AF.add_arguments(args)

    def initialise_random_agent(self, agent: BoatAgent):
        """
        Receives an empty BoatAgent and initialises properties with acceptable random values.
        :param agent: uninitialised BoatAgent.
        """

        def sample(prob):
            if type(prob) is dict:
                return random.choices(list(prob.keys()), list(prob.values()), k=1)[0]
            elif type(prob) is list:
                return random.choice(prob)

        # Probabilities for BoatCategory.
        boat_category_prob = {BoatCategory.Civilian: 0.2,
                              BoatCategory.Corporate: 0.2,
                              BoatCategory.Police: 0.1,
                              BoatCategory.CoastGuard: 0.1,
                              BoatCategory.Military: 0.4}
        agent.BoatCategory = sample(boat_category_prob)

        # Probabilities for TaskedStatus. Civilians are never "tasked".
        if agent.BoatCategory == BoatCategory.Civilian:
            tasked_status_prob = {TaskedStatus.AtEase: 0.5,
                                  TaskedStatus.Returning: 0.5}
        else:
            tasked_status_prob = {TaskedStatus.AtEase: 0.2,
                                  TaskedStatus.Returning: 0.3,
                                  TaskedStatus.Tasked: 0.5}

        agent.TaskedStatus = sample(tasked_status_prob)

        # Probabilities for TaskNature. Different rules for Civilians, Corporate and others.
        if agent.BoatCategory == BoatCategory.Civilian:
            task_nature_prob = {TaskNature.Leisure: 0.4,
                                TaskNature.Sport: 0.3,
                                TaskNature.Training: 0.3}
        elif agent.BoatCategory == BoatCategory.Corporate:
            task_nature_prob = {TaskNature.Training: 0.4,
                                TaskNature.Trade: 0.6}
        elif agent.BoatCategory < BoatCategory.Military:
            task_nature_prob = {TaskNature.Training: 0.2,
                                TaskNature.Patrol: 0.4,
                                TaskNature.Pursuit: 0.4}
        else:  # if Military
            task_nature_prob = {TaskNature.Training: 0.4,
                                TaskNature.Patrol: 0.2,
                                TaskNature.Pursuit: 0.1,
                                TaskNature.Combat: 0.3}
        agent.TaskNature = sample(task_nature_prob)

        # Probabilities for EmergencyNature.
        emergency_nature_prob = {EmergencyNature.NoEmergency: 0.85,
                                 EmergencyNature.Mechanical: 0.05,
                                 EmergencyNature.SickPassenger: 0.05,
                                 EmergencyNature.Fire: 0.05}
        agent.EmergencyNature = sample(emergency_nature_prob)

        # Probabilities for PayloadType.
        payload_type_prob = {PayloadType.Empty: 0.5,
                             PayloadType.Food: 0.25,
                             PayloadType.MedicalSupplies: 0.25}
        agent.PayloadType = sample(payload_type_prob)

        # Probabilities for SensitivePayload. Different rules for Civ/Corp and armed forces.
        if agent.BoatCategory < BoatCategory.Police:
            agent.SensitivePayload = SensitivePayload.NoSensitivePayload
        else:  # From police onwards.
            sensitive_payload_prob = {SensitivePayload.NoSensitivePayload: 0.6,
                                      SensitivePayload.Weapons: 0.3,
                                      SensitivePayload.WantedPrisoner: 0.1}
            agent.SensitivePayload = sample(sensitive_payload_prob)

        # Probabilities for DiplomaticCredentials.
        if agent.BoatCategory < BoatCategory.Police:
            diplomatic_prob = {DiplomaticCredentials.NoCredentials: 0.6,
                               DiplomaticCredentials.Diplomat: 0.2,
                               DiplomaticCredentials.UnitedNations: 0.2}
            agent.DiplomaticCredentials = sample(diplomatic_prob)
        else:
            agent.DiplomaticCredentials = DiplomaticCredentials.NoCredentials

        # Probabilities for MilitaryRank.
        if agent.BoatCategory != BoatCategory.Military:
            agent.MilitaryRank = MilitaryRank.NoRank
        else:
            agent.MilitaryRank = sample(list(MilitaryRank))

        # Probabilities for VIPIdentity.
        agent.VIPIdentity = sample(list(VIPIdentity))

        # Probabilities for SuperVIP.
        super_vip_prob = {SuperVIP.NoSuperVIP: 0.8,
                          SuperVIP.PrimeMinister: 0.15,
                          SuperVIP.HeadOfState: 0.05}
        agent.SuperVIP = sample(super_vip_prob)

        # Probabilities for UndercoverOps.
        if agent.BoatCategory <= BoatCategory.Corporate:
            undercover_prob = {UndercoverOps.NoSpy: 0.7,
                               UndercoverOps.Spy: 0.3}
            agent.UndercoverOps = sample(undercover_prob)
        else:
            agent.UndercoverOps = UndercoverOps.NoSpy

        agent.VehicleCost = sample(list(VehicleCost))
        agent.VehicleAge = sample(list(VehicleAge))

    def define_attacks(self):
        """
        Defines attack relationships present in the culture.
        """
        ID = self.ids
        attack = self.AF.add_attack

        # Attacks to motion.
        attack(ID["higher_category"], ID["motion"])
        attack(ID["tasked_status"], ID["motion"])
        attack(ID["has_emergency"], ID["motion"])
        attack(ID["payload_type"], ID["motion"])
        attack(ID["sensitive_payload"], ID["motion"])
        attack(ID["diplomatic_credentials"], ID["motion"])
        attack(ID["vip_identity"], ID["motion"])
        attack(ID["super_vip"], ID["motion"])
        attack(ID["vehicle_cost"], ID["motion"])
        attack(ID["vehicle_age"], ID["motion"])

        # Attacks to vehicle_age.
        attack(ID["higher_category"], ID["vehicle_age"])
        attack(ID["tasked_status"], ID["vehicle_age"])
        attack(ID["has_emergency"], ID["vehicle_age"])
        attack(ID["payload_type"], ID["vehicle_age"])
        attack(ID["sensitive_payload"], ID["vehicle_age"])
        attack(ID["diplomatic_credentials"], ID["vehicle_age"])
        attack(ID["vip_identity"], ID["vehicle_age"])
        attack(ID["super_vip"], ID["vehicle_age"])
        attack(ID["vehicle_cost"], ID["vehicle_age"])

        # Attacks to vehicle_cost.
        attack(ID["higher_category"], ID["vehicle_cost"])
        attack(ID["tasked_status"], ID["vehicle_cost"])
        attack(ID["has_emergency"], ID["vehicle_cost"])
        attack(ID["payload_type"], ID["vehicle_cost"])
        attack(ID["sensitive_payload"], ID["vehicle_cost"])
        attack(ID["diplomatic_credentials"], ID["vehicle_cost"])
        attack(ID["vip_identity"], ID["vehicle_cost"])
        attack(ID["super_vip"], ID["vehicle_cost"])

        # Attacks to higher_category.
        attack(ID["tasked_status"], ID["higher_category"])
        attack(ID["has_emergency"], ID["higher_category"])
        attack(ID["sensitive_payload"], ID["higher_category"])
        attack(ID["diplomatic_credentials"], ID["higher_category"])
        attack(ID["super_vip"], ID["higher_category"])
        attack(ID["military_rank"], ID["higher_category"])
        attack(ID["undercover_ops"], ID["higher_category"])

        # Attacks to tasked_status.
        attack(ID["task_nature"], ID["tasked_status"])
        attack(ID["has_emergency"], ID["tasked_status"])
        attack(ID["sensitive_payload"], ID["tasked_status"])
        attack(ID["diplomatic_credentials"], ID["tasked_status"])
        attack(ID["vip_identity"], ID["tasked_status"])
        attack(ID["super_vip"], ID["tasked_status"])
        attack(ID["undercover_ops"], ID["tasked_status"])

        # Attacks to payload_type.
        attack(ID["has_emergency"], ID["payload_type"])
        attack(ID["sensitive_payload"], ID["payload_type"])
        attack(ID["task_nature"], ID["payload_type"])
        attack(ID["diplomatic_credentials"], ID["payload_type"])
        attack(ID["super_vip"], ID["payload_type"])
        attack(ID["military_rank"], ID["payload_type"])

        # Attacks to task_nature.
        attack(ID["has_emergency"], ID["task_nature"])
        attack(ID["sensitive_payload"], ID["task_nature"])
        attack(ID["diplomatic_credentials"], ID["task_nature"])
        attack(ID["military_rank"], ID["task_nature"])
        attack(ID["super_vip"], ID["task_nature"])
        attack(ID["undercover_ops"], ID["task_nature"])

        # Attacks to vip_identity.
        attack(ID["has_emergency"], ID["vip_identity"])
        attack(ID["sensitive_payload"], ID["vip_identity"])
        attack(ID["super_vip"], ID["vip_identity"])
        attack(ID["diplomatic_credentials"], ID["vip_identity"])
        attack(ID["military_rank"], ID["vip_identity"])
        attack(ID["undercover_ops"], ID["vip_identity"])

        # Attacks to military_rank.
        attack(ID["has_emergency"], ID["military_rank"])
        attack(ID["sensitive_payload"], ID["military_rank"])
        attack(ID["super_vip"], ID["military_rank"])
        attack(ID["diplomatic_credentials"], ID["military_rank"])
        attack(ID["undercover_ops"], ID["military_rank"])

        # Attacks to diplomatic_credentials.
        attack(ID["has_emergency"], ID["diplomatic_credentials"])
        attack(ID["super_vip"], ID["diplomatic_credentials"])
        attack(ID["sensitive_payload"], ID["diplomatic_credentials"])

        # Attacks to sensitive_payload.
        attack(ID["has_emergency"], ID["sensitive_payload"])
        attack(ID["super_vip"], ID["sensitive_payload"])
        attack(ID["undercover_ops"], ID["sensitive_payload"])

        # Attacks to undercover_ops.
        attack(ID["has_emergency"], ID["undercover_ops"])
        attack(ID["super_vip"], ID["undercover_ops"])

        # Attacks to has_emergency.
        attack(ID["super_vip"], ID["has_emergency"])

    def generate_bw_framework(self):
        """
        This function generates and populates a black-and-white framework (forced bipartition) from an existing culture.
        A black-and-white framework is built with the following rules:
        1. Every argument is represented by 4 nodes, black and white X hypothesis and verified.
        2. Every attack between arguments is reconstructed between nodes of different colours.
        :return: A flat black-and-white framework.
        """
        self.raw_bw_framework = ArgumentationFramework()
        for argument in self.AF.arguments():
            # Even indices for defender, odd for challenger.
            # Adding hypothetical arguments.
            black_hypothesis = PrivateArgument(arg_id = argument.id() * 4,
                                               descriptive_text = argument.hypothesis_text,
                                               privacy_cost = argument.privacy_cost)
            white_hypothesis = PrivateArgument(arg_id = argument.id() * 4 + 1,
                                               descriptive_text = argument.hypothesis_text,
                                               privacy_cost = argument.privacy_cost)
            h_verifier = argument.hypothesis_verifier if argument.hypothesis_verifier else always_true
            black_hypothesis.set_verifier(h_verifier)
            white_hypothesis.set_verifier(h_verifier)

            # Adding verified arguments.
            black_verified = PrivateArgument(arg_id=argument.id() * 4 + 2,
                                             descriptive_text=argument.verified_fact_text,
                                             privacy_cost=argument.privacy_cost)
            white_verified = PrivateArgument(arg_id=argument.id() * 4 + 3,
                                             descriptive_text=argument.verified_fact_text,
                                             privacy_cost=argument.privacy_cost)
            f_verifier = argument.fact_verifier if argument.fact_verifier else argument.verifier()
            black_verified.set_verifier(f_verifier)
            white_verified.set_verifier(f_verifier)

            self.raw_bw_framework.add_arguments([black_hypothesis, white_hypothesis, black_verified, white_verified])

            # Adding mutual attacks between contradictory hypotheses.
            self.raw_bw_framework.add_attack(black_hypothesis.id(), white_hypothesis.id())
            self.raw_bw_framework.add_attack(white_hypothesis.id(), black_hypothesis.id())

            # Adding mutual attacks between contradictory verified arguments.
            self.raw_bw_framework.add_attack(black_verified.id(), white_verified.id())
            self.raw_bw_framework.add_attack(white_verified.id(), black_verified.id())

            # Adding attacks between immediate verified and hypothetical arguments.
            self.raw_bw_framework.add_attack(black_verified.id(), white_hypothesis.id())
            self.raw_bw_framework.add_attack(white_verified.id(), black_hypothesis.id())

        # Adding attacks between different arguments in original framework.
        # Each hypothesis attacks both the attacked hypothesis and verified arguments.
        for attacker_id, attacked_set in self.AF.attacks().items():
            black_hypothesis_attacker_id = attacker_id * 4
            white_hypothesis_attacker_id = attacker_id * 4 + 1

            # Reproducing previous attacks, crossing between black and white nodes.
            for attacked_id in attacked_set:
                black_hypothesis_attacked_id = attacked_id * 4
                white_hypothesis_attacked_id = attacked_id * 4 + 1
                black_verified_attacked_id = attacked_id * 4 + 2
                white_verified_attacked_id = attacked_id * 4 + 3
                self.raw_bw_framework.add_attack(black_hypothesis_attacker_id, white_hypothesis_attacked_id)
                self.raw_bw_framework.add_attack(black_hypothesis_attacker_id, white_verified_attacked_id)
                self.raw_bw_framework.add_attack(white_hypothesis_attacker_id, black_hypothesis_attacked_id)
                self.raw_bw_framework.add_attack(white_hypothesis_attacker_id, black_verified_attacked_id)