int main() {
    student_Type drv_obj;
    std::cout << std::fixed << std::setprecision(4);
    std::cout << drv_obj.f_Calculate_Gpax(30.0f, 9.0f) << "\n";
    std::cout << drv_obj.f_Calculate_Gpax(10.0f, 0.0f) << "\n";
    std::cout << drv_obj.f_Calculate_Gpax(50.0f, 10.0f) << "\n";
    return 0;
}
