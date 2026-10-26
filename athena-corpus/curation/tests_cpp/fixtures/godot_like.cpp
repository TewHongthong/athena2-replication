#define MY_MAX(a, b) ((a) > (b) ? (a) : (b))

namespace Demo {

enum Mode {
	MODE_IDLE,
	MODE_RUN = 2,
};

template <typename T>
class Holder {
	T value;

public:
	T get() const { return value; }
};

class Widget : public Base {
	GDCLASS(Widget, Base);

	static const int MAX_ITEMS = 8;
	int item_count = 0;
	Vector<int> *items = nullptr;
	bool _dirty = false;

public:
	enum State { STATE_OFF, STATE_ON };

	Widget();
	~Widget();

	void set_count(int p_count);
	int get_count() const;
	bool operator==(const Widget &p_other) const;
	static Widget *create(const String &p_name, int &r_error);
};

Widget::Widget() :
		item_count(0), _dirty(false) {
	items = memnew(Vector<int>);
}

Widget::~Widget() {
	memdelete(items);
}

void Widget::set_count(int p_count) {
	ERR_FAIL_COND(p_count < 0);
	int old_count = item_count;
	item_count = p_count;
	auto notify = [&](int p_value) {
		print_line(itos(p_value));
	};
	for (const String &name : names) {
		notify(name.length());
	}
	if (old_count < item_count && item_count > 4) {
		_dirty = true;
	}
}

Widget *Widget::create(const String &p_name, int &r_error) {
	Widget *result = memnew(Widget);
	r_error = 0;
	return result;
}

} // namespace Demo
