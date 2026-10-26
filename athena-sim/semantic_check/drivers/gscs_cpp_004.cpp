int main() {
    pupil_Type drv_obj;
    drv_obj.Set_Name(std::string("Bob"));
    std::cout << drv_obj.str_student_name << "\n";
    drv_obj.Set_Name(std::string(40, 'Z'));
    std::cout << drv_obj.str_student_name << " " << drv_obj.str_student_name.size() << "\n";
    return 0;
}
