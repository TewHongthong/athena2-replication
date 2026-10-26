class DrvMain {
    public static void main(String[] args) throws Exception {
        System.out.println(String.format("%.4f", temperature_Type.f_Convert_Celsius("212")));
        System.out.println(String.format("%.4f", temperature_Type.f_Convert_Celsius("abc")));
        System.out.println(String.format("%.4f", temperature_Type.f_Convert_Celsius("98.6")));
    }
}
