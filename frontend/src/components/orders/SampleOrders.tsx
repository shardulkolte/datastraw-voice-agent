import { Card, Col, Row, Tag, Typography } from "antd";

const orders = [
  {
    id: "ORD-101",
    customer: "Priya Sharma",
    product: "Vitamin C Serum (30ml)",
    amount: "₹699",
    status: "Out for Delivery",
    tracking: "BlueDart · BD-982103",
    notes: "Expected by 6 PM today",
  },
  {
    id: "ORD-102",
    customer: "Rahul Verma",
    product: "Hydrating Sunscreen SPF 50",
    amount: "₹499",
    status: "Delivered",
    tracking: "Delhivery · DL-441029",
    notes: "Delivered 14 days ago",
  },
  {
    id: "ORD-103",
    customer: "Ananya Patel",
    product: "Green Tea Face Wash + Toner",
    amount: "₹850",
    status: "Processing",
    tracking: "Not yet shipped",
    notes: "Ordered 3 hours ago",
  },
];

export default function SampleOrders() {
  return (
    <Row gutter={[12, 12]}>
      {orders.map((order) => (
        <Col xs={24} key={order.id}>
          <Card size="small" className="order-card">
            <div className="order-card-top">
              <Typography.Text strong>{order.id}</Typography.Text>
              <Typography.Text strong>{order.amount}</Typography.Text>
            </div>

            <Typography.Text>{order.product}</Typography.Text>
            <Typography.Text type="secondary" className="order-customer">
              {order.customer}
            </Typography.Text>

            <Tag
              color={
                order.status === "Delivered"
                  ? "green"
                  : order.status === "Processing"
                    ? "blue"
                    : "gold"
              }
            >
              {order.status}
            </Tag>

            <Typography.Text className="order-detail">
              {order.tracking}
            </Typography.Text>
            <Typography.Text type="secondary" className="order-detail">
              {order.notes}
            </Typography.Text>
          </Card>
        </Col>
      ))}
    </Row>
  );
}
