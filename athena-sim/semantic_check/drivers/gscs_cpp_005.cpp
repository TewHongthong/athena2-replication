int main() {
    float drv_a[] = {3.5f, 9.25f, -1.0f, 9.0f};
    float drv_b[] = {-5.0f, -2.0f};
    std::cout << std::fixed << std::setprecision(4);
    std::cout << f_Find_Maximum(drv_a, 4) << "\n";
    std::cout << f_Find_Maximum(drv_b, 2) << "\n";
    std::cout << f_Find_Maximum(drv_a, 1) << "\n";
    return 0;
}
