package hello;

public class HelloWorld {
    private String msg;

    public HelloWorld () {
        msg = "Hello World!!!";
    }

    public void setMessage(String message) {
        msg = message;
    }

    public String getMessage () {
        return msg;
    }
}
