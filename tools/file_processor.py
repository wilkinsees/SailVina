import os
import shutil
import copy
from itertools import product

from tools.configer import Configer
from tools.check import Check
from tools.format_convertor import extract_pdbqt, smi_2_mol
from tools.file_path import substituents_path


def pdbqt2dir(pdbqt_path):
    """
    在相同路径创建一个该名字的文件夹，将pdbqt文件移动进去。\n
    比如pdbqt_path = ./Proteins/a.pdbqt
    :param pdbqt_path: pdbqt文件路径
    """
    # 1.创建文件夹
    pdbqt_dir = pdbqt_path[0:-6]
    os.mkdir(pdbqt_dir)
    # 2.移动文件
    target_path = pdbqt_dir + os.sep + "preped.pdbqt"
    shutil.move(pdbqt_path, target_path)


def gen_config_file(output_name, x, y, z, size):
    """
    根据x,y,z,size生成config文件
    :param output_name: 输出路径文件名
    :param x: x坐标
    :param y: y坐标
    :param z: z坐标
    :param size: 盒子大小
    """
    exhaustiveness = Configer.get_para("exhaustiveness") if Configer.get_para("exhaustiveness") != "" else 8
    num_modes = Configer.get_para("num_modes") if Configer.get_para("num_modes") != "" else 9
    energy_range = Configer.get_para("energy_range") if Configer.get_para("energy_range") != "" else 3
    with open(output_name, "w") as f:
        f.writelines("center_x = " + str(x) + "\n")
        f.writelines("center_y = " + str(y) + "\n")
        f.writelines("center_z = " + str(z) + "\n")
        f.writelines("size_x = " + str(size) + "\n")
        f.writelines("size_y = " + str(size) + "\n")
        f.writelines("size_z = " + str(size) + "\n")
        f.writelines("exhaustiveness = " + exhaustiveness + "\n")
        f.writelines("num_modes = " + num_modes + "\n")
        f.writelines("energy_range = " + energy_range + "\n")


def get_config_files(protein_path):
    """
    获取一个路径中的config文件
    :param protein_path: 蛋白文件夹路径，比如"./Proteins/01"
    :return: 蛋白的config文件列表
    """
    files = os.listdir(protein_path)
    config_files = []
    for file in files:
        if file.startswith("config"):
            config_files.append(protein_path + os.sep + file)
    return config_files


def mk_output_dir(file_path):
    """
    如果不存在就创建输出文件夹
    :param file_path: 目标文件夹
    """
    if not os.path.exists(file_path):
        os.mkdir(file_path)


def remove_dir_if_exist(rm_dir):
    if os.path.exists(rm_dir):
        shutil.rmtree(rm_dir)


def create_scores_file(output_file, scores_dict, mode=0):
    """
    创建分数文件
    :param output_file: 输出目录
    :param scores_dict:分数字典，包含受体/配体/分数
    :param mode 为0表示分数字典有受体，1表示只有配体。
    """
    with open(output_file, "w") as f:
        if mode == 0:
            f.write("receptor_name\tligand_name\tscores\n")
            for receptor in scores_dict:
                for ligand in scores_dict[receptor]:
                    # 如果列表只有一个元素
                    if not isinstance(scores_dict[receptor][ligand], list):
                        f.write(receptor + "\t" + ligand + "\t" + scores_dict[receptor][ligand] + "\n")
                    else:
                        for score in scores_dict[receptor][ligand]:
                            f.write(receptor + "\t" + ligand + "\t" + score + "\n")
        if mode == 1:
            f.write("ligand_name\tscores\n")
            for ligand in scores_dict:
                # 如果列表只有一个元素
                if not isinstance(scores_dict[ligand], list):
                    f.write(ligand + "\t" + scores_dict[ligand] + "\n")
                else:
                    for score in scores_dict[ligand]:
                        f.write(ligand + "\t" + score + "\n")


def get_best_scores(scores_dict):
    """
    传入分数字典，将分数最小的输出，多个都输出。
    :param scores_dict: 分数列表
    :return: 最小的配体字典
    """
    # 获取分数最低的值
    tmp_dict = copy.deepcopy(scores_dict)
    for receptor in scores_dict:
        min_score = 0
        for ligand in scores_dict[receptor]:
            score = float(scores_dict[receptor][ligand])
            if score <= min_score:
                min_score = score

        for ligand in scores_dict[receptor]:
            if float(scores_dict[receptor][ligand]) > min_score:
                # 删除分数大于最小值的字典
                tmp_dict[receptor].pop(ligand)

    return tmp_dict


def extract_file(output_file, extract_folder):
    """
    读取分数文件，提取配体到指定文件夹
    :param output_file: 分数文件，txt格式
    :param extract_folder: 输出目录
    :return 读取成功为True，否则为False
    """
    # 判断文件所在位置
    with open(output_file) as f:
        line1 = f.readline()
        # 有受体
        if line1.startswith("receptor_name"):
            # 文件所在位置不正确
            if not Check.next_path_has_pdbqt(os.path.split(output_file)[0]):
                print("%s所在路径不正确，请确保在受体文件夹中" % output_file)
                return False

            # 读取剩余内容
            lines = f.readlines()
            for line in lines:
                receptor_name = line.split()[0]
                ligand_name = line.split()[1]
                extract_receptor_file(os.path.split(output_file)[0],
                                      receptor_name, ligand_name,
                                      extract_folder)
            return True
        # 只有配体
        elif line1.startswith("ligand_name"):
            # 文件所在位置不正确
            if not Check.path_has_pdbqt(os.path.split(output_file)[0]):
                print("%s所在路径不正确，请确保在配体文件夹中" % output_file)
                return False

            # 读取剩余内容
            lines = f.readlines()
            for line in lines:
                ligand_name = line.split()[0]
                extract_ligand_file(os.path.split(output_file)[0],
                                    ligand_name, extract_folder)
            return True
        else:
            print("%s读取不是指定文件" % output_file)
            return False


def extract_receptor_file(root_folder, receptor_name, ligand_name, output_folder):
    """
    从有受体的文件夹提取配体
    :param root_folder: 根目录
    :param receptor_name: 受体名
    :param ligand_name: 配体名
    :param output_folder: 输出目录
    """
    # 创建输出文件夹
    output_dir = os.path.join(output_folder, receptor_name)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    pdbqt_file = os.path.join(root_folder, receptor_name, ligand_name)
    extract_pdbqt(pdbqt_file, output_dir, index=1)


def extract_ligand_file(root_folder, ligand_name, output_folder):
    """
    从有配体的文件夹提取配体
    :param root_folder: 根目录
    :param ligand_name: 配体名
    :param output_folder: 输出目录
    """
    pdbqt_file = os.path.join(root_folder, ligand_name)
    extract_pdbqt(pdbqt_file, output_folder, index=1)


def gen_smi_der(raw_smi: str, output_path):
    """
    根据提供的含有R的smi生成取代基衍生物，生成mol格式到输出目录
    :param raw_smi: 含有R的smi表达式
    :param output_path: 输出路径
    """
    der_smi = gen_smi(raw_smi)
    i = 0
    while i < len(der_smi):
        output_file = os.path.join(output_path, str(i)) + ".mol"
        smi_2_mol(der_smi[i], output_file)
        i += 1


def gen_smi(raw_smi: str):
    """
    根据提供的含有R的smi表达式产生新的smi
    :param raw_smi: 含有R的smi的表达式
    :return: 生成的smi列表
    """
    new_smi = []
    # 根据[R]来切分字符串
    split_smi = raw_smi.split("[R]")

    # 第一种情况：第一个为[R],其他没有
    if split_smi[0] == "" and len(split_smi) == 2:
        for sub in read_subs(1):
            new_smi.append(sub + split_smi[1])

    # 第二种情况，中间为[R]，可以有1个或者多个
    # [R]的个数
    r_count = len(split_smi) - 1
    if split_smi[0] != "":
        # 生成排列组合
        sub_list = list(product(read_subs(0), repeat=r_count))
        for sub in sub_list:
            i = 0
            smi = split_smi[0]
            while i < r_count:
                smi += "(" + sub[i] + ")" + split_smi[i + 1]
                i += 1
            new_smi.append(smi)

    # 第三种情况，开头有个[R]，中间还有[R]
    if split_smi[0] == "" and len(split_smi) > 2:
        for first_sub in read_subs(1):
            sub_list = list(product(read_subs(0), repeat=(r_count - 1)))
            for sub in sub_list:
                i = 0
                smi = first_sub + split_smi[1]
                while i < (r_count - 1):
                    smi += "(" + sub[i] + ")" + split_smi[i + 2]
                    i += 1
                new_smi.append(smi)

    return new_smi


def read_subs(position: int):
    """
    读取取代基配置文件
    :param position: R所在的位置。1表示在第一位，0表示在其他位置
    :return: 取代基表示列表
    """
    sub_list = []
    with open(substituents_path, encoding='UTF-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("#") or line == "\n":
                continue
            if line.startswith("H"):
                sub_list.append("")
                continue
            if position == 0:
                sub_list.append(line.split(" = ")[1].strip())
            elif position == 1:
                if len(line.split(" = ")) == 3:
                    sub_list.append(line.split(" = ")[2].strip())
                else:
                    sub_list.append(line.split(" = ")[1].strip())
    return sub_list


def get_backbone(file):
    """
    获取一个pdb文件的骨架
    :param file: pdb文件
    :return: 骨架
    """
    backbone = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            # HETATM    1  C   UNL     1      21.020   0.624  28.104  1.00  0.00      topt C
            if line.startswith("HETATM") or line.startswith("ATOM"):
                atom = line.split()[2]
                if atom != "H":
                    backbone.append(atom)
    return backbone


def get_ligand_position(file):
    """
    返回pdb文件的坐标
    :param file: pdb文件
    :return: 坐标文件列表
    """
    position = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            # HETATM    1  C   UNL     1      21.020   0.624  28.104  1.00  0.00      topt C
            if line.startswith("HETATM") or line.startswith("ATOM"):
                info = line.split()
                atom = info[2]
                if atom != "H":
                    position.append([info[5], info[6], info[7]])
    return position


if __name__ == '__main__':
    # 本地调试代码
    gen_smi_der("[R]C(C=C1)=CC=C1C2=CC=CC=C2", "D:\\Desktop")
