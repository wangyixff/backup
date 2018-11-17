from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Categories, Base, CategoryItem, User

engine = create_engine('sqlite:///dbfile/catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# user 1
User1 = User(email="yifan@ualberta.ca", name="wangyixff")

session.add(User1)
session.commit()

# Soccer category
category1 = Categories(name="Soccer", user_id=1, user=User1)

session.add(category1)
session.commit()

CategoryItem1 = CategoryItem(name="Balls", description="Thermally\
                             bonded seamless surface for more\
                             predictable trajectory, better touch\
                             and lower water uptake",
                             category_name="Soccer", category=category1,
                             user_id=1, user=User1)

session.add(CategoryItem1)
session.commit()


CategoryItem2 = CategoryItem(name="Cleats", description="Perforated heel\
                             lining with a suede-like finish grips the\
                             foot and helps hold the boot in place.",
                             category_name="Soccer", category=category1,
                             user_id=1, user=User1)

session.add(CategoryItem2)
session.commit()


# Hockey category
category2 = Categories(name="Hockey", user_id=1, user=User1)

session.add(category2)
session.commit()


CategoryItem1 = CategoryItem(name="Hockey stick", description="\
                             technology used in building the\
                             shafts results in incredibly light\
                             and durable shafts. Blades are made\
                             by hand, and uses high performance\
                             foams and a carbon bridge that give\
                             increased durability and blade\
                             stiffness",
                             category_name="Hockey",
                             category=category2,
                             user_id=1, user=User1)

session.add(CategoryItem1)
session.commit()


# Baseball category
category3 = Categories(name="Baseball", user_id=1, user=User1)

session.add(category3)
session.commit()


CategoryItem1 = CategoryItem(name="Bats", description="With a\
                             sleek matte finish, this bat is\
                             made of bamboo to deliver\
                             durability and reliable\
                             performance. ",
                             category_name="Baseball",
                             category=category3, user_id=1,
                             user=User1)

session.add(CategoryItem1)
session.commit()


print("Added category and items!")
