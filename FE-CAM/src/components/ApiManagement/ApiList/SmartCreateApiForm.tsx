import { Form, Input } from "@cloud-materials/common";
import styles from "../index.module.less";

export const SmartCreateApiTitle: React.FC = () => (
    <span className={styles.aiMenuContent}>
        <span className={styles.aiMenuGradientText}>智能创建 API</span>
    </span>
);

const SmartCreateApiForm: React.FC = () => {
    return (
        <Form.Item
            field="prompt"
            label="API 描述"
            rules={[{ required: true, message: "请输入 API 相关描述" }]}
        >
            <Input.TextArea
                autoSize={{ minRows: 6, maxRows: 12 }}
                allowClear
                placeholder="请明确包含请求方法和路径（如：GET /users/{user_id} 查询用户资料）；请求方法 + 路径不得与已有 API 重复"
            />
        </Form.Item>
    );
};

export default SmartCreateApiForm;
