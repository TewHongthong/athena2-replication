class DrvMain {
    public static void main(String[] args) throws Exception {
        account_Type drv_obj = new account_Type();
        drv_obj.Deposit_Money(5.0);
        drv_obj.Deposit_Money(0.5);
        drv_obj.Deposit_Money(2.25);
        java.lang.reflect.Field drv_field = account_Type.class.getDeclaredField("d_balance");
        drv_field.setAccessible(true);
        System.out.println(drv_field.get(drv_obj));
    }
}
